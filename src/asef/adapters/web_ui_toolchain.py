from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .docker import CommandExecutor, ContainerResult, DockerPolicy, DockerRunner


WEB_UI_IMAGE = "asef/web-ui-playwright:1.61.0"
NODE_VERSION = "24.16.0"
PLAYWRIGHT_VERSION = "1.61.0"
CHROMIUM_VERSION = "149.0.7827.55"
MAX_PROBE_BYTES = 64 * 1024
_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


class WebUiToolchainError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class WebUiToolchainProbeResult:
    status: str
    node_version: str
    playwright_version: str
    chromium_version: str | None
    uid: int | None
    gid: int | None
    headless: bool
    rootfs_read_only: bool
    workspace_read_only: bool
    egress_blocked: bool
    diagnostic_code: str | None = None
    schema_version: str = "1.0.0"

    def validate(self) -> None:
        if self.schema_version != "1.0.0" or self.status not in {"PASSED", "ERROR"}:
            raise WebUiToolchainError("invalid Web UI toolchain probe header")
        if self.node_version != NODE_VERSION or self.playwright_version != PLAYWRIGHT_VERSION:
            raise WebUiToolchainError("Web UI toolchain versions do not match the pinned contract")
        if self.chromium_version is not None and (
            not isinstance(self.chromium_version, str)
            or not 1 <= len(self.chromium_version) <= 100
            or any(ord(character) < 32 for character in self.chromium_version)
        ):
            raise WebUiToolchainError("invalid Chromium version evidence")
        for value, label in ((self.uid, "uid"), (self.gid, "gid")):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise WebUiToolchainError(f"{label} must be a non-negative integer or null")
        controls = (
            self.headless,
            self.rootfs_read_only,
            self.workspace_read_only,
            self.egress_blocked,
        )
        if any(not isinstance(value, bool) for value in controls):
            raise WebUiToolchainError("Web UI isolation observations must be booleans")
        if self.status == "PASSED":
            if (
                self.chromium_version != CHROMIUM_VERSION
                or self.uid in {None, 0}
                or self.gid is None
                or not all(controls)
                or self.diagnostic_code is not None
            ):
                raise WebUiToolchainError("passed Web UI toolchain probe violates pinned controls")
        elif self.diagnostic_code not in {
            "BROWSER_START_FAILED",
            "ISOLATION_CONTROL_FAILED",
            "SANDBOX_EXECUTION_ERROR",
        }:
            raise WebUiToolchainError("error probe requires an allowlisted diagnostic")

    @classmethod
    def infrastructure_error(cls) -> "WebUiToolchainProbeResult":
        return cls(
            status="ERROR",
            node_version=NODE_VERSION,
            playwright_version=PLAYWRIGHT_VERSION,
            chromium_version=None,
            uid=None,
            gid=None,
            headless=True,
            rootfs_read_only=False,
            workspace_read_only=False,
            egress_blocked=False,
            diagnostic_code="SANDBOX_EXECUTION_ERROR",
        )


def web_ui_toolchain_probe_from_dict(raw: Any) -> WebUiToolchainProbeResult:
    fields = {
        "schema_version", "status", "node_version", "playwright_version",
        "chromium_version", "uid", "gid", "headless", "rootfs_read_only",
        "workspace_read_only", "egress_blocked", "diagnostic_code",
    }
    if not isinstance(raw, dict) or set(raw) != fields:
        raise WebUiToolchainError("Web UI toolchain probe fields do not match schema 1.0.0")
    try:
        result = WebUiToolchainProbeResult(**raw)
    except TypeError as exc:
        raise WebUiToolchainError("Web UI toolchain probe contains invalid fields") from exc
    result.validate()
    return result


class DockerWebUiToolchainProbe:
    command = ("probe",)

    def __init__(
        self,
        allowed_workspace_root: Path,
        executor: CommandExecutor = subprocess.run,
        *,
        image: str = WEB_UI_IMAGE,
        timeout_seconds: int = 30,
    ) -> None:
        self.allowed_workspace_root = allowed_workspace_root
        self.executor = executor
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.last_container: ContainerResult | None = None
        self.last_image_id: str | None = None

    @staticmethod
    def stage(root: Path) -> tuple[Path, Path]:
        workspace = root / "workspace"
        output = root / "output"
        workspace.mkdir(parents=True, exist_ok=False)
        output.mkdir(parents=True, exist_ok=False)
        (workspace / "fixture.txt").write_text("ASEF Web UI toolchain probe\n", encoding="utf-8")
        native_path = output / "toolchain-result.json"
        native_path.write_text("", encoding="utf-8")
        native_path.chmod(0o666)
        return workspace, output

    def execute(self, workspace: Path, output_dir: Path) -> WebUiToolchainProbeResult:
        image_id = self._resolve_image_id()
        self.last_image_id = image_id
        native_path = output_dir / "toolchain-result.json"
        native_path.write_text("", encoding="utf-8")
        native_path.chmod(0o666)
        runner = DockerRunner(
            DockerPolicy(
                image=image_id,
                capability_id="web-ui-toolchain",
                allowed_workspace_root=self.allowed_workspace_root,
                cpus=1,
                memory="512m",
                pids_limit=128,
                timeout_seconds=self.timeout_seconds,
                stdout_limit_bytes=32 * 1024,
                stderr_limit_bytes=32 * 1024,
            ),
            self.executor,
        )
        container = runner.run(workspace, list(self.command), output_dir=output_dir)
        self.last_container = container
        if container.timed_out or not container.cleanup_succeeded:
            return WebUiToolchainProbeResult.infrastructure_error()
        try:
            if not native_path.is_file() or not 0 < native_path.stat().st_size <= MAX_PROBE_BYTES:
                raise WebUiToolchainError("Web UI toolchain result is missing or oversized")
            raw = json.loads(native_path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
            result = web_ui_toolchain_probe_from_dict(raw)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return WebUiToolchainProbeResult.infrastructure_error()
        if container.exit_code == 0 and result.status == "PASSED":
            return result
        if container.exit_code != 0 and result.status == "ERROR":
            return result
        return WebUiToolchainProbeResult.infrastructure_error()

    def _resolve_image_id(self) -> str:
        completed = self.executor(
            ["docker", "image", "inspect", self.image, "--format", "{{.Id}}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        image_id = completed.stdout.strip().lower()
        if completed.returncode != 0 or not _IMAGE_ID.fullmatch(image_id):
            raise OSError(
                f"Web UI tool image {self.image!r} is unavailable or has an invalid image ID"
            )
        return image_id


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise WebUiToolchainError(f"duplicate JSON key in Web UI toolchain result: {key}")
        value[key] = item
    return value
