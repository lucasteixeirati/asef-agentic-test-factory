from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import unittest
from uuid import uuid4

from asef.adapters.java_unit_execution import DockerJavaUnitExecutor, java_unit_functional_fingerprint
from asef.java_unit_contracts import java_unit_plan_from_dict


@unittest.skipUnless(os.environ.get("ASEF_RUN_JAVA_DOCKER_TESTS") == "1", "Java Docker tests disabled")
class JavaUnitConformanceDockerTests(unittest.TestCase):
    def test_executable_cases_repeat_with_stable_functional_fingerprints(self):
        manifest = json.loads(Path("examples/java-junit/conformance/manifest.json").read_text(encoding="utf-8"))
        Path(".asef").mkdir(exist_ok=True)
        for case in (item for item in manifest["cases"] if item["expected_outcome"] in {"PASSED", "ASSERTION_FAILURE"}):
            fingerprints = []
            for _ in range(manifest["repetitions"]):
                root = Path(".asef") / f"java-conformance-{uuid4().hex}"; root.mkdir()
                try:
                    workspace, output = DockerJavaUnitExecutor.stage(java_unit_plan_from_dict(case["plan"]), root)
                    result = DockerJavaUnitExecutor(root).execute(workspace, output)
                finally:
                    shutil.rmtree(root)
                self.assertEqual(case["expected_outcome"], result.outcome.value)
                fingerprints.append(java_unit_functional_fingerprint(result))
            self.assertEqual(1, len(set(fingerprints)))


if __name__ == "__main__": unittest.main()
