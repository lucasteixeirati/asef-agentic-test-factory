from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from asef.adapters.oracle_workspace import IsolatedOracleWorkspaceAdapter
from asef.adapters.pytest_execution import PytestDockerAdapter
from asef.adapters.run_store import JsonRunStore
from asef.adapters.workspace import EphemeralWorkspaceAdapter
from asef.application.alpha_evaluation import AlphaEvaluationCoordinator
from asef.application.correct_test import CorrectionLoopController
from asef.application.execute_generated import ExecuteGeneratedAttemptService
from asef.application.execute_oracle import ExecuteOracleService
from asef.application.ports import ResolvedQualityContext
from asef.context import QualityContext
from asef.contracts import SkeletonRunRequest, SkeletonRunState, UnitTestArtifact
from asef.outcomes import RunClassification, RunStatus
from asef.skills.unit import UnitSkill


RUN_DOCKER = os.getenv("ASEF_RUN_DOCKER_TESTS") == "1"


class UnusedCorrector:
    def correct(self, request, previous, feedback):
        raise AssertionError("happy-path Docker evaluation must not request correction")


@unittest.skipUnless(RUN_DOCKER, "Docker tests disabled")
class AlphaOracleDockerIntegrationTests(unittest.TestCase):
    def test_generated_and_oracle_pass_in_separate_readonly_workspaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            sut = repository / "sut"
            sut.mkdir(parents=True)
            (sut / "calculator.py").write_text(
                "def add(left, right):\n    return left + right\n",
                encoding="utf-8",
            )
            oracle = repository / "datasets/SMK-001/oracle/test_oracle.py"
            oracle.parent.mkdir(parents=True)
            oracle.write_text(
                "from calculator import add\n\ndef test_oracle_add():\n    assert add(-2, 2) == 0\n",
                encoding="utf-8",
            )
            request = SkeletonRunRequest(
                context_ref="examples/context/walking-skeleton-context.json",
                system_id="calculator-service",
                requested_skill="unit",
                requirement_title="Docker alpha oracle",
                requirement_description="compare generated pytest evidence with a curated oracle",
            )
            quality = QualityContext.load(Path("examples/context/walking-skeleton-context.json"))
            context = ResolvedQualityContext(quality.snapshot_for(request), sut, ("calculator.py",))
            output_root = root / "runs"
            output_root.mkdir()
            state = SkeletonRunState(request, run_id="alpha-docker")
            store = JsonRunStore(output_root)
            run_dir = store.save_prepared(state, context.snapshot)
            executor = PytestDockerAdapter(output_root)
            coordinator = AlphaEvaluationCoordinator(
                ExecuteGeneratedAttemptService(EphemeralWorkspaceAdapter(), executor, store),
                ExecuteOracleService(IsolatedOracleWorkspaceAdapter(repository), executor, store),
                CorrectionLoopController(UnusedCorrector(), UnitSkill()),
                store,
            )
            artifact = UnitTestArtifact(
                "tests_generated/test_add.py",
                "from calculator import add\n\ndef test_generated_add():\n    assert add(2, 3) == 5\n",
                ("SCN-001",),
            )

            result = coordinator.execute(
                state,
                run_dir,
                context,
                artifact,
                "datasets/SMK-001/oracle/test_oracle.py",
            )

            self.assertEqual((result.state.status, result.state.classification), (RunStatus.SUCCEEDED, RunClassification.ACCEPTED))
            self.assertTrue((run_dir / "attempts/000/generated/execution.json").is_file())
            self.assertTrue((run_dir / "attempts/000/oracle/execution.json").is_file())
            self.assertTrue((run_dir / "attempts/000/evaluation.json").is_file())
            self.assertTrue((run_dir / "artifacts/attempt-001/tests_generated/test_add.py").is_file())
            self.assertTrue((run_dir / "oracle/test_oracle.py").is_file())
            self.assertFalse((run_dir / "oracle-workspace").exists())
            self.assertFalse((run_dir / "attempt-workspaces").exists())


if __name__ == "__main__":
    unittest.main()
