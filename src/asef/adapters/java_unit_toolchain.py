from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Any

from .docker import CommandExecutor, ContainerResult, DockerPolicy, DockerRunner


JAVA_UNIT_IMAGE = "asef/java-junit:21.0.11"
JAVA_VERSION = "21.0.11"
MAVEN_VERSION = "3.9.16"
JUNIT_VERSION = "5.13.4"
SUREFIRE_VERSION = "3.5.5"
MAX_PROBE_BYTES = 64 * 1024
_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


class JavaUnitToolchainError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class JavaUnitToolchainProbeResult:
    status: str
    java_version: str
    maven_version: str
    junit_version: str
    surefire_version: str
    uid: int | None
    gid: int | None
    rootfs_read_only: bool
    workspace_read_only: bool
    egress_blocked: bool
    offline_cache_ready: bool
    diagnostic_code: str | None = None
    schema_version: str = "1.0.0"

    def validate(self) -> None:
        if self.schema_version != "1.0.0" or self.status not in {"PASSED", "ERROR"}:
            raise JavaUnitToolchainError("invalid Java unit toolchain probe header")
        if (self.java_version, self.maven_version, self.junit_version, self.surefire_version) != (
            JAVA_VERSION, MAVEN_VERSION, JUNIT_VERSION, SUREFIRE_VERSION,
        ):
            raise JavaUnitToolchainError("Java unit toolchain versions do not match pinned values")
        for value, label in ((self.uid, "uid"), (self.gid, "gid")):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise JavaUnitToolchainError(f"{label} must be a non-negative integer or null")
        controls = (self.rootfs_read_only, self.workspace_read_only, self.egress_blocked, self.offline_cache_ready)
        if any(not isinstance(value, bool) for value in controls):
            raise JavaUnitToolchainError("Java unit isolation observations must be booleans")
        if self.status == "PASSED":
            if self.uid in {None, 0} or self.gid is None or not all(controls) or self.diagnostic_code is not None:
                raise JavaUnitToolchainError("passed Java unit toolchain probe violates pinned controls")
        elif self.diagnostic_code not in {"ISOLATION_CONTROL_FAILED", "SANDBOX_EXECUTION_ERROR"}:
            raise JavaUnitToolchainError("error probe requires an allowlisted diagnostic")

    @classmethod
    def infrastructure_error(cls) -> "JavaUnitToolchainProbeResult":
        return cls("ERROR", JAVA_VERSION, MAVEN_VERSION, JUNIT_VERSION, SUREFIRE_VERSION,
                   None, None, False, False, False, False, "SANDBOX_EXECUTION_ERROR")


def java_unit_toolchain_probe_from_dict(raw: Any) -> JavaUnitToolchainProbeResult:
    fields = {
        "schema_version", "status", "java_version", "maven_version", "junit_version",
        "surefire_version", "uid", "gid", "rootfs_read_only", "workspace_read_only",
        "egress_blocked", "offline_cache_ready", "diagnostic_code",
    }
    if not isinstance(raw, dict) or set(raw) != fields:
        raise JavaUnitToolchainError("Java unit toolchain probe fields do not match schema 1.0.0")
    try:
        result = JavaUnitToolchainProbeResult(**raw)
    except TypeError as exc:
        raise JavaUnitToolchainError("Java unit toolchain probe contains invalid fields") from exc
    result.validate()
    return result


class DockerJavaUnitToolchainProbe:
    def __init__(self, allowed_workspace_root: Path, executor: CommandExecutor = subprocess.run,
                 *, image: str = JAVA_UNIT_IMAGE, timeout_seconds: int = 30) -> None:
        self.allowed_workspace_root = allowed_workspace_root
        self.executor = executor
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.last_container: ContainerResult | None = None
        self.last_image_id: str | None = None

    @staticmethod
    def stage(root: Path) -> tuple[Path, Path]:
        workspace, output = root / "workspace", root / "output"
        workspace.mkdir(parents=True, exist_ok=False)
        output.mkdir(parents=True, exist_ok=False)
        (workspace / "fixture.txt").write_text("ASEF Java unit toolchain probe\n", encoding="utf-8")
        native = output / "toolchain-result.json"
        native.write_text("", encoding="utf-8")
        native.chmod(0o666)
        return workspace, output

    def execute(self, workspace: Path, output: Path) -> JavaUnitToolchainProbeResult:
        image_id = self._resolve_image_id()
        self.last_image_id = image_id
        native = output / "toolchain-result.json"
        native.write_text("", encoding="utf-8")
        native.chmod(0o666)
        runner = DockerRunner(DockerPolicy(
            image=image_id, capability_id="java-unit-toolchain",
            allowed_workspace_root=self.allowed_workspace_root, cpus=1, memory="512m",
            pids_limit=128, timeout_seconds=self.timeout_seconds,
            stdout_limit_bytes=32 * 1024, stderr_limit_bytes=32 * 1024,
        ), self.executor)
        container = runner.run(workspace, ["probe"], output_dir=output)
        self.last_container = container
        if container.timed_out or not container.cleanup_succeeded:
            return JavaUnitToolchainProbeResult.infrastructure_error()
        try:
            if not native.is_file() or not 0 < native.stat().st_size <= MAX_PROBE_BYTES:
                raise JavaUnitToolchainError("Java unit probe result is missing or oversized")
            raw = json.loads(native.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
            result = java_unit_toolchain_probe_from_dict(raw)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return JavaUnitToolchainProbeResult.infrastructure_error()
        if (container.exit_code == 0) == (result.status == "PASSED"):
            return result
        return JavaUnitToolchainProbeResult.infrastructure_error()

    def _resolve_image_id(self) -> str:
        completed = self.executor(
            ["docker", "image", "inspect", self.image, "--format", "{{.Id}}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15, check=False,
        )
        image_id = completed.stdout.strip().lower()
        if completed.returncode != 0 or not _IMAGE_ID.fullmatch(image_id):
            raise OSError(f"Java unit tool image {self.image!r} is unavailable or has an invalid image ID")
        return image_id


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise JavaUnitToolchainError(f"duplicate JSON key in Java unit toolchain result: {key}")
        value[key] = item
    return value
