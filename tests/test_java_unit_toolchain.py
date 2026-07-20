from __future__ import annotations

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from asef.adapters.java_unit_toolchain import (
    DockerJavaUnitToolchainProbe, JavaUnitToolchainError, JavaUnitToolchainProbeResult,
    java_unit_toolchain_probe_from_dict,
)


class JavaUnitToolchainTests(unittest.TestCase):
    def valid(self):
        return JavaUnitToolchainProbeResult(
            "PASSED", "21.0.11", "3.9.16", "5.13.4", "3.5.5", 65534, 65534,
            True, True, True, True,
        )

    def test_probe_contract_accepts_only_pinned_nonroot_isolated_toolchain(self):
        result = self.valid()
        result.validate()
        raw = result.__dict__ if hasattr(result, "__dict__") else {
            field: getattr(result, field) for field in result.__dataclass_fields__
        }
        self.assertEqual(result, java_unit_toolchain_probe_from_dict(raw))
        for change in ({"uid": 0}, {"maven_version": "LATEST"}, {"egress_blocked": False}):
            changed = raw | change
            with self.subTest(change=change), self.assertRaises(JavaUnitToolchainError):
                java_unit_toolchain_probe_from_dict(changed)

    def test_probe_rejects_duplicate_json_keys(self):
        duplicate = '{"schema_version":"1.0.0","schema_version":"1.0.0"}'
        with self.assertRaises(JavaUnitToolchainError):
            json.loads(duplicate, object_pairs_hook=__import__(
                "asef.adapters.java_unit_toolchain", fromlist=["_strict_object"]
            )._strict_object)

    def test_error_probe_and_infrastructure_fallback_are_strict(self):
        raw = {field: getattr(JavaUnitToolchainProbeResult.infrastructure_error(), field)
               for field in JavaUnitToolchainProbeResult.__dataclass_fields__}
        self.assertEqual("SANDBOX_EXECUTION_ERROR", java_unit_toolchain_probe_from_dict(raw).diagnostic_code)
        raw["diagnostic_code"] = "UNKNOWN"
        with self.assertRaises(JavaUnitToolchainError): java_unit_toolchain_probe_from_dict(raw)

    def test_missing_image_is_rejected_before_probe(self):
        def executor(command, **kwargs):
            del kwargs
            return subprocess.CompletedProcess(command, 1, "", "missing")
        with TemporaryDirectory() as temporary:
            with self.assertRaises(OSError): DockerJavaUnitToolchainProbe(Path(temporary), executor)._resolve_image_id()

    def test_adapter_resolves_tag_to_image_id_and_returns_native_result(self):
        image_id = "sha256:" + "a" * 64
        probe = self.valid()
        raw = {field: getattr(probe, field) for field in probe.__dataclass_fields__}

        def executor(command, **kwargs):
            if command[:3] == ["docker", "image", "inspect"]:
                return subprocess.CompletedProcess(command, 0, image_id + "\n", "")
            if command[:3] == ["docker", "ps", "-aq"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            output_spec = command[command.index("--mount", command.index("--mount") + 1) + 1]
            output_path = Path(output_spec.split("src=", 1)[1].split(",dst=", 1)[0])
            (output_path / "toolchain-result.json").write_text(json.dumps(raw), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace, output = DockerJavaUnitToolchainProbe.stage(root)
            adapter = DockerJavaUnitToolchainProbe(root, executor)
            result = adapter.execute(workspace, output)
        self.assertEqual("PASSED", result.status)
        self.assertEqual(image_id, adapter.last_image_id)


if __name__ == "__main__": unittest.main()
