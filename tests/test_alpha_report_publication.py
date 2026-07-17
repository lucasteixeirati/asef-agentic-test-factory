from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from asef.adapters.context_file import FileQualityContextAdapter
from asef.adapters.run_store import JsonRunStore
from asef.application.prepare_run import PrepareRunService
from asef.contracts import EvidenceRef, SkeletonRunRequest
from asef.outcomes import RunClassification, RunStatus
from asef.report_contracts import (
    EvidenceIntegrityStatus,
    alpha_run_report_from_dict,
)


def request(title: str = "Add integers") -> SkeletonRunRequest:
    return SkeletonRunRequest(
        context_ref="examples/context/walking-skeleton-context.json",
        system_id="calculator-service",
        requested_skill="unit",
        requirement_title=title,
        requirement_description="Return the arithmetic sum of two integers",
    )


def terminal_run(root: Path, title: str = "Add integers"):
    store = JsonRunStore(root)
    prepared = PrepareRunService(FileQualityContextAdapter(), store).execute(request(title))
    state = prepared.state
    artifact_path = prepared.run_dir / "artifacts/attempt-001/tests_generated/test_unit.py"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text("def test_add():\n    assert 1 + 1 == 2\n", encoding="utf-8")
    digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    state.evidence_refs.append(
        EvidenceRef(
            "unit_test_artifact",
            "artifacts/attempt-001/tests_generated/test_unit.py",
            digest,
        )
    )
    state.facts["analysis"] = {
        "behaviors": ["Return the arithmetic sum"],
        "risks": ["Boundary values may be mishandled"],
        "scenarios": ["Add two positive integers"],
    }
    state.facts["artifact"] = {
        "relative_path": "artifacts/attempt-001/tests_generated/test_unit.py",
        "sha256": digest,
        "scenario_ids": ["SCN-001"],
    }
    state.facts["execution"] = {"outcome": "PASSED"}
    state.status = RunStatus.SUCCEEDED
    state.classification = RunClassification.ACCEPTED
    evaluation = {
        "accepted": True,
        "tests": 1,
        "passed": 1,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
    }
    return store, prepared.run_dir, state, evaluation


class AlphaReportPublicationTests(unittest.TestCase):
    def test_store_persists_normative_report_manifest_hashes_and_idempotent_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, run_dir, state, evaluation = terminal_run(Path(directory))
            self.assertEqual(store.save_report(state, None, evaluation), "report.md")
            first_json = (run_dir / "report.json").read_bytes()
            first_markdown = (run_dir / "report.md").read_bytes()

            report = alpha_run_report_from_dict(json.loads(first_json))
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(report.functional_result.accepted)
            self.assertEqual(
                manifest["reports"]["json"]["sha256"],
                hashlib.sha256(first_json).hexdigest(),
            )
            self.assertEqual(
                manifest["reports"]["markdown"]["sha256"],
                hashlib.sha256(first_markdown).hexdigest(),
            )

            store.save_report(state, None, evaluation)
            self.assertEqual((run_dir / "report.json").read_bytes(), first_json)
            self.assertEqual((run_dir / "report.md").read_bytes(), first_markdown)

    def test_evidence_hash_mismatch_is_explicit_without_changing_terminal_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, run_dir, state, evaluation = terminal_run(Path(directory))
            state.evidence_refs[0] = EvidenceRef(
                state.evidence_refs[0].kind,
                state.evidence_refs[0].relative_path,
                "0" * 64,
            )
            state.facts["artifact"]["sha256"] = "0" * 64
            store.save_report(state, None, evaluation)
            report = alpha_run_report_from_dict(
                json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            )
            artifact_evidence = next(
                item for item in report.evidence if item.kind == "unit-test-artifact"
            )
            self.assertIs(artifact_evidence.integrity_status, EvidenceIntegrityStatus.MISMATCH)
            self.assertFalse(artifact_evidence.publishable)
            self.assertIn(
                "EVIDENCE_INTEGRITY_FAILURE",
                {item.limitation_code for item in report.limitations},
            )
            self.assertEqual(
                (report.status, report.classification),
                (RunStatus.SUCCEEDED, RunClassification.ACCEPTED),
            )

    def test_markdown_escapes_public_input_and_cannot_add_a_new_fact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, run_dir, state, evaluation = terminal_run(
                Path(directory), "Unsafe | `heading` <tag>"
            )
            store.save_report(state, None, evaluation)
            markdown = (run_dir / "report.md").read_text(encoding="utf-8")
            self.assertIn("Unsafe \\| \\`heading\\` &lt;tag&gt;", markdown)
            self.assertNotIn("<tag>", markdown)
            self.assertIn("FACT-FUNCTIONAL-ACCEPTED", markdown)

    def test_terminal_before_artifact_still_receives_a_bounded_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = JsonRunStore(root)
            prepared = PrepareRunService(FileQualityContextAdapter(), store).execute(request())
            prepared.state.status = RunStatus.POLICY_BLOCKED
            prepared.state.classification = RunClassification.POLICY_VIOLATION
            store.save_report(
                prepared.state,
                None,
                {"accepted": False, "tests": None, "passed": None, "failed": None},
            )
            report = alpha_run_report_from_dict(
                json.loads((prepared.run_dir / "report.json").read_text(encoding="utf-8"))
            )
            self.assertTrue(report.terminal)
            self.assertEqual(report.artifacts, ())
            self.assertFalse(report.functional_result.accepted)

    def test_report_transaction_restores_all_files_when_one_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, run_dir, state, evaluation = terminal_run(Path(directory))
            store.save_report(state, None, evaluation)
            paths = tuple(run_dir / name for name in ("report.json", "report.md", "manifest.json"))
            before = {path: path.read_bytes() for path in paths}
            state.usage.elapsed_ms = 1
            original_replace = Path.replace
            calls = 0

            def fail_second(source: Path, target: Path) -> Path:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated report transaction failure")
                return original_replace(source, target)

            with patch.object(Path, "replace", fail_second), self.assertRaisesRegex(
                OSError, "simulated report transaction failure"
            ):
                store.save_report(state, None, evaluation)

            self.assertEqual({path: path.read_bytes() for path in paths}, before)
            self.assertEqual(
                [path for path in run_dir.iterdir() if path.name.startswith(".tmp-")],
                [],
            )

    def test_missing_evidence_is_reported_and_existing_report_tamper_blocks_reissue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, run_dir, state, evaluation = terminal_run(Path(directory))
            state.evidence_refs.append(
                EvidenceRef("normalized_execution", "results/missing.json", "1" * 64)
            )
            store.save_report(state, None, evaluation)
            report = alpha_run_report_from_dict(
                json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            )
            missing = next(
                item for item in report.evidence if item.relative_path == "results/missing.json"
            )
            self.assertIs(missing.integrity_status, EvidenceIntegrityStatus.MISSING)
            self.assertIn(
                "EVIDENCE_INTEGRITY_FAILURE",
                {item.limitation_code for item in report.limitations},
            )

            (run_dir / "report.md").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(OSError, "manifest report hash"):
                store.save_report(state, None, evaluation)


if __name__ == "__main__":
    unittest.main()
