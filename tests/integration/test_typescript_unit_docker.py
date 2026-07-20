from __future__ import annotations
import os, shutil, unittest
from pathlib import Path
from uuid import uuid4
from asef.adapters.typescript_unit_execution import DockerTypeScriptUnitExecutor
from asef.contracts import TestExecutionOutcome
from asef.java_unit_contracts import JavaUnitScenario, JavaUnitTestPlan

@unittest.skipUnless(os.environ.get("ASEF_RUN_WEB_UI_DOCKER_TESTS") == "1", "Web UI Docker tests disabled")
class TypeScriptUnitDockerTests(unittest.TestCase):
    def test_same_reviewed_intention_passes_and_wrong_oracle_fails(self):
        Path(".asef").mkdir(exist_ok=True)
        for expected, outcome in ((5, TestExecutionOutcome.PASSED), (99, TestExecutionOutcome.ASSERTION_FAILURE)):
            plan = JavaUnitTestPlan("JAV-TS-001", (JavaUnitScenario("SCN-ADD", "Add", "add", 2, 3, expected),))
            root = Path(".asef") / f"ts-unit-{uuid4().hex}"; root.mkdir()
            try:
                workspace, output = DockerTypeScriptUnitExecutor.stage(plan, root)
                result = DockerTypeScriptUnitExecutor(root).execute(workspace, output)
            finally: shutil.rmtree(root)
            self.assertIs(result.outcome, outcome)

if __name__ == "__main__": unittest.main()
