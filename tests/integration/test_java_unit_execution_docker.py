from __future__ import annotations

import os
from pathlib import Path
import shutil
import unittest
from uuid import uuid4

from asef.adapters.java_unit_execution import DockerJavaUnitExecutor
from asef.contracts import TestExecutionOutcome
from asef.java_unit_contracts import JavaUnitScenario, JavaUnitTestPlan


@unittest.skipUnless(os.environ.get("ASEF_RUN_JAVA_DOCKER_TESTS") == "1", "Java Docker tests disabled")
class JavaUnitExecutionDockerTests(unittest.TestCase):
    def test_passing_and_assertion_failure_are_normalized_from_surefire(self):
        Path(".asef").mkdir(exist_ok=True)
        for expected, outcome in ((5, TestExecutionOutcome.PASSED), (99, TestExecutionOutcome.ASSERTION_FAILURE)):
            plan = JavaUnitTestPlan("JAV-DOCKER-001", (
                JavaUnitScenario("SCN-ADD", "Add values", "add", 2, 3, expected),
            ))
            root = Path(".asef") / f"java-execution-{uuid4().hex}"
            root.mkdir()
            try:
                workspace, output = DockerJavaUnitExecutor.stage(plan, root)
                result = DockerJavaUnitExecutor(root).execute(workspace, output)
            finally:
                shutil.rmtree(root)
            self.assertIs(result.outcome, outcome)
            self.assertEqual((result.tests, result.failed), (1, 0 if expected == 5 else 1))
            self.assertIsNotNone(result.raw_result_content)


if __name__ == "__main__": unittest.main()
