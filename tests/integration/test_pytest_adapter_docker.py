from __future__ import annotations

import hashlib
import os
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from asef.adapters.pytest_execution import PytestDockerAdapter
from asef.context import QualityContext
from asef.contracts import SkeletonRunRequest, TestExecutionOutcome


@unittest.skipUnless(os.environ.get("ASEF_RUN_DOCKER_TESTS") == "1", "Docker tests disabled")
class PytestAdapterDockerIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(".asef") / f"pytest-adapter-{uuid4().hex}"
        self.workspace = self.root / "workspace"
        (self.workspace / "tests_generated").mkdir(parents=True)
        self.context = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
        request = SkeletonRunRequest(
            context_ref="examples/context/walking-skeleton-context.json",
            system_id="calculator-service",
            requested_skill="unit",
            requirement_title="pytest adapter integration",
            requirement_description="execute pytest in the isolated runtime",
        )
        self.snapshot = self.context.snapshot_for(request)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def execute(self):
        return PytestDockerAdapter(Path(".asef")).execute(self.workspace, self.snapshot)

    def test_assertion_failure_is_normalized_and_workspace_is_readonly(self) -> None:
        source = self.workspace / "sut.py"
        source.write_text("VALUE = 1\n", encoding="utf-8")
        original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        (self.workspace / "tests_generated/test_result.py").write_text(
            "from pathlib import Path\n"
            "import pytest\n\n"
            "def test_pass(): assert 1 == 1\n"
            "def test_failure(): assert 1 == 2\n"
            "def test_workspace_readonly():\n"
            "    with pytest.raises(OSError): Path('sut.py').write_text('changed')\n",
            encoding="utf-8",
        )
        result = self.execute()
        self.assertIs(result.outcome, TestExecutionOutcome.ASSERTION_FAILURE)
        self.assertEqual((result.tests, result.passed, result.failed, result.errors), (3, 2, 1, 0))
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original_hash)
        self.assertIsNotNone(result.raw_result_content)

    def test_syntax_collection_error_is_test_error(self) -> None:
        (self.workspace / "tests_generated/test_invalid.py").write_text(
            "def test_invalid(:\n    pass\n", encoding="utf-8"
        )
        result = self.execute()
        self.assertIs(result.outcome, TestExecutionOutcome.TEST_ERROR)
        self.assertGreaterEqual(result.errors or 0, 1)

    def test_empty_suite_is_no_tests(self) -> None:
        result = self.execute()
        self.assertIs(result.outcome, TestExecutionOutcome.NO_TESTS)
        self.assertEqual(result.tests, 0)


if __name__ == "__main__":
    unittest.main()
