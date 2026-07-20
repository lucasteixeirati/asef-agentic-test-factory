from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import subprocess
import tempfile
import unittest

from asef.adapters.web_ui_toolchain import (
    CHROMIUM_VERSION,
    DockerWebUiToolchainProbe,
    NODE_VERSION,
    PLAYWRIGHT_VERSION,
    WebUiToolchainError,
    WebUiToolchainProbeResult,
    web_ui_toolchain_probe_from_dict,
)


IMAGE_ID = "sha256:" + "a" * 64
ROOT = Path(__file__).resolve().parents[1]


def passing_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "status": "PASSED",
        "node_version": NODE_VERSION,
        "playwright_version": PLAYWRIGHT_VERSION,
        "chromium_version": CHROMIUM_VERSION,
        "uid": 65534,
        "gid": 65534,
        "headless": True,
        "rootfs_read_only": True,
        "workspace_read_only": True,
        "egress_blocked": True,
        "diagnostic_code": None,
    }


class WebUiToolchainContractTests(unittest.TestCase):
    def test_passing_probe_is_strict_and_pinned(self) -> None:
        result = web_ui_toolchain_probe_from_dict(passing_payload())
        self.assertEqual("PASSED", result.status)
        self.assertEqual(CHROMIUM_VERSION, result.chromium_version)

    def test_probe_rejects_version_drift_root_and_missing_control(self) -> None:
        for field, value in (
            ("node_version", "25.0.0"),
            ("playwright_version", "1.62.0"),
            ("chromium_version", "149.0.0.0"),
            ("uid", 0),
            ("egress_blocked", False),
        ):
            payload = passing_payload()
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(WebUiToolchainError):
                web_ui_toolchain_probe_from_dict(payload)

    def test_probe_rejects_unknown_fields_and_unlisted_diagnostic(self) -> None:
        payload = passing_payload()
        payload["stdout"] = "untrusted"
        with self.assertRaisesRegex(WebUiToolchainError, "fields do not match"):
            web_ui_toolchain_probe_from_dict(payload)

    def test_tooling_is_digest_lockfile_and_closed_driver(self) -> None:
        root = ROOT / "tooling" / "web-ui-playwright"
        dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
        lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
        driver = (root / "asef_web_ui_driver.mjs").read_text(encoding="utf-8")
        self.assertIn("FROM mcr.microsoft.com/playwright@sha256:", dockerfile)
        self.assertIn("npm ci --omit=dev --ignore-scripts", dockerfile)
        self.assertIn("PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1", dockerfile)
        self.assertIn("ARG SOURCE_DATE_EPOCH=0", dockerfile)
        self.assertNotIn("npm install ", dockerfile)
        self.assertEqual(3, lock["lockfileVersion"])
        self.assertEqual("1.61.0", lock["packages"]["node_modules/@playwright/test"]["version"])
        self.assertEqual("1.61.0", lock["packages"]["node_modules/playwright"]["version"])
        self.assertEqual("1.61.0", lock["packages"]["node_modules/playwright-core"]["version"])
        self.assertIn('["version", "probe", "run", "unit-run"]', driver)
        self.assertIn('"--test", "--test-reporter=tap", "/workspace/generated/asef-generated.test.ts"', driver)
        for forbidden in ("eval(", "new Function", "process.env.OPENAI"):
            self.assertNotIn(forbidden, driver)
        error = WebUiToolchainProbeResult.infrastructure_error()
        error.validate()
        with self.assertRaisesRegex(WebUiToolchainError, "allowlisted diagnostic"):
            replace(error, diagnostic_code="ARBITRARY").validate()


class DockerWebUiToolchainProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        Path(".asef").mkdir(exist_ok=True)

    @staticmethod
    def fake_with_payload(payload: dict[str, object], *, container_exit: int = 0):
        commands: list[list[str]] = []

        def fake(command, **kwargs):
            del kwargs
            commands.append(command)
            if command[:3] == ["docker", "image", "inspect"]:
                return subprocess.CompletedProcess(command, 0, IMAGE_ID + "\n", "")
            if command[:2] == ["docker", "run"]:
                output_mount = next(item for item in command if item.endswith("dst=/asef-output"))
                source = output_mount.split(",src=", 1)[1].rsplit(",dst=", 1)[0]
                (Path(source) / "toolchain-result.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )
                return subprocess.CompletedProcess(command, container_exit, "", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        return commands, fake

    def test_probe_uses_closed_command_and_hardened_container_policy(self) -> None:
        commands, fake = self.fake_with_payload(passing_payload())
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiToolchainProbe.stage(root)
            adapter = DockerWebUiToolchainProbe(root, fake)
            result = adapter.execute(workspace, output)
        docker_run = next(command for command in commands if command[:2] == ["docker", "run"])
        self.assertEqual("PASSED", result.status)
        self.assertEqual(IMAGE_ID, adapter.last_image_id)
        self.assertEqual(["probe"], docker_run[-1:])
        self.assertEqual("none", docker_run[docker_run.index("--network") + 1])
        self.assertEqual("65534:65534", docker_run[docker_run.index("--user") + 1])
        self.assertIn("--read-only", docker_run)
        self.assertIn("--cap-drop", docker_run)
        self.assertIn("no-new-privileges:true", docker_run)
        self.assertIn("com.asef.capability=web-ui-toolchain", docker_run)
        self.assertNotIn("--ipc", docker_run)

    def test_invalid_or_spoofed_native_result_fails_closed(self) -> None:
        invalid = passing_payload()
        invalid["uid"] = 0
        commands, fake = self.fake_with_payload(invalid)
        del commands
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiToolchainProbe.stage(root)
            result = DockerWebUiToolchainProbe(root, fake).execute(workspace, output)
        self.assertEqual("ERROR", result.status)
        self.assertEqual("SANDBOX_EXECUTION_ERROR", result.diagnostic_code)

    def test_driver_error_is_preserved_only_with_matching_exit(self) -> None:
        error = passing_payload()
        error.update({
            "status": "ERROR",
            "chromium_version": None,
            "rootfs_read_only": False,
            "diagnostic_code": "BROWSER_START_FAILED",
        })
        commands, fake = self.fake_with_payload(error, container_exit=1)
        del commands
        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiToolchainProbe.stage(root)
            result = DockerWebUiToolchainProbe(root, fake).execute(workspace, output)
        self.assertEqual("BROWSER_START_FAILED", result.diagnostic_code)

    def test_missing_or_invalid_image_is_rejected_before_container(self) -> None:
        def fake(command, **kwargs):
            del kwargs
            return subprocess.CompletedProcess(command, 1, "", "missing")

        with tempfile.TemporaryDirectory(dir=".asef") as directory:
            root = Path(directory)
            workspace, output = DockerWebUiToolchainProbe.stage(root)
            with self.assertRaisesRegex(OSError, "tool image"):
                DockerWebUiToolchainProbe(root, fake).execute(workspace, output)


if __name__ == "__main__":
    unittest.main()
