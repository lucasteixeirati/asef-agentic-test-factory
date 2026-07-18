from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.gate5_evidence_check import (
    Gate5EvidenceChecker,
    TASK_IDS,
    validate_external_result_payload,
    validate_internal_result_payload,
)


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/project/gates/gate-05-evidence-inventory.json"


def _fixture_payload() -> dict[str, object]:
    payload = copy.deepcopy(json.loads(INVENTORY.read_text(encoding="utf-8")))
    external = payload["external_evaluation"]
    assert isinstance(external, dict)
    external["protocol_version"] = "1.0.1"
    external["protocol"] = "protocol.md"
    external["template"] = "template.md"
    external.pop("participant_kit", None)
    external.pop("facilitator_checklist", None)
    external.pop("preflight", None)
    internal = payload["internal_evaluation"]
    assert isinstance(internal, dict)
    internal["protocol"] = "internal-protocol.md"
    internal["status"] = "READY_FOR_SESSION"
    internal["results"] = []
    internal.pop("summary", None)
    criteria = payload["criteria"]
    assert isinstance(criteria, list)
    for criterion in criteria:
        assert isinstance(criterion, dict)
        criterion["evidence"] = ["evidence.md"]
    return payload


def _write_fixture(root: Path, payload: dict[str, object]) -> None:
    inventory = root / "docs/project/gates/gate-05-evidence-inventory.json"
    inventory.parent.mkdir(parents=True)
    inventory.write_text(json.dumps(payload), encoding="utf-8")
    (root / "evidence.md").write_text("# Evidence\n", encoding="utf-8")
    (root / "protocol.md").write_text(
        "# Protocol\n\n**Versão:** `1.0.1`\n\n## Escopo e versão congelada\n\n"
        "v0.1.0a7 79fbeb0dbbef39799801b86cebd59f8b55edaa0a "
        "f492e1ca693a307991d805f91bf5283d89c1867e52121e7eb26ed13a1c06f9ad "
        "d6b111b7b07f8029a703f4ae59e8a628406e5fe149a1cb6617937608eefa55af\n\n"
        "## Regras do facilitador\n\n## Tarefas\n\n## Rubrica congelada\n",
        encoding="utf-8",
    )
    (root / "template.md").write_text(
        "# Template\n\n## Controle da sessão\n\n## Elegibilidade e consentimento\n\n"
        "## Tarefas\n\n## Findings\n",
        encoding="utf-8",
    )
    (root / "internal-protocol.md").write_text(
        "# Internal\n\n## Natureza e limite da evidência\n\nINFORMATIVE_INTERNAL\n\n"
        "## Consentimento e canal\n\n## Escopo congelado\n\nv0.1.0a7 "
        "79fbeb0dbbef39799801b86cebd59f8b55edaa0a\n\n"
        "## Regras do facilitador\n\n## Uso no Gate 5\n",
        encoding="utf-8",
    )


def _valid_result() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "protocol_version": "1.0.1",
        "participant_id": "P01",
        "consent_obtained": True,
        "session_status": "VALID",
        "interpretation_correct": True,
        "eligibility": {
            "qe_experience": True,
            "external_to_authoring": True,
            "no_individual_briefing": True,
        },
        "tasks": [{"id": task_id, "state": "COMPLETED_INDEPENDENTLY"} for task_id in TASK_IDS],
        "findings": [],
        "privacy": {
            "pii_removed": True,
            "material_raw_not_versioned": True,
            "review_or_withdrawal_honored": True,
        },
    }


def _valid_internal_result() -> dict[str, object]:
    return json.loads(
        (ROOT / "docs/evaluations/2026-07-18-alpha-python-internal-evaluation-I01.json").read_text(
            encoding="utf-8"
        )
    )


class Gate5EvidenceCheckerTests(unittest.TestCase):
    def test_repository_inventory_passes_and_has_twenty_criteria(self) -> None:
        audit = Gate5EvidenceChecker(ROOT).run()
        self.assertTrue(audit.passed, list(audit.findings))
        self.assertEqual(audit.checked_criteria, 20)
        self.assertGreaterEqual(audit.checked_evidence, 40)

    def test_missing_criterion_and_unsafe_evidence_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _fixture_payload()
            criteria = payload["criteria"]
            assert isinstance(criteria, list)
            criteria.pop()
            first = criteria[0]
            assert isinstance(first, dict)
            first["evidence"] = ["../outside.md"]
            _write_fixture(root, payload)
            audit = Gate5EvidenceChecker(root).run()
        codes = {item.code for item in audit.findings}
        self.assertIn("CRITERIA_IDS", codes)
        self.assertIn("EVIDENCE_PATH_UNSAFE", codes)

    def test_inventory_revision_is_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _fixture_payload()
            payload["inventory_revision"] = "1.0.0"
            _write_fixture(root, payload)
            audit = Gate5EvidenceChecker(root).run()
        self.assertIn("INVENTORY_REVISION", {item.code for item in audit.findings})

    def test_ci_requires_exactly_the_seven_canonical_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _fixture_payload()
            runs = payload["ci_runs"]
            assert isinstance(runs, list) and isinstance(runs[0], dict)
            runs[0]["jobs"] = ["core", "core"]
            _write_fixture(root, payload)
            audit = Gate5EvidenceChecker(root).run()
        self.assertIn("CI_JOBS", {item.code for item in audit.findings})

    def test_frozen_asset_digest_cannot_be_replaced_by_another_valid_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _fixture_payload()
            release = payload["release"]
            assert isinstance(release, dict)
            assets = release["assets"]
            assert isinstance(assets, list) and isinstance(assets[0], dict)
            assets[0]["digest"] = "sha256:" + ("0" * 64)
            _write_fixture(root, payload)
            audit = Gate5EvidenceChecker(root).run()
        self.assertIn("ASSET_FROZEN_DIVERGENCE", {item.code for item in audit.findings})

    def test_partial_criterion_cannot_recommend_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _fixture_payload()
            decision = payload["decision"]
            assert isinstance(decision, dict)
            decision["technical_recommendation"] = "APPROVE"
            criteria = payload["criteria"]
            assert isinstance(criteria, list) and isinstance(criteria[0], dict)
            criteria[0]["status"] = "PARTIAL"
            _write_fixture(root, payload)
            audit = Gate5EvidenceChecker(root).run()
        self.assertIn("DECISION_CONTRADICTION", {item.code for item in audit.findings})

    def test_preflight_cannot_be_ready_with_failed_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _fixture_payload()
            external = payload["external_evaluation"]
            assert isinstance(external, dict)
            external["preflight"] = "preflight.json"
            preflight = json.loads(
                (ROOT / "docs/evaluations/2026-07-18-alpha-python-release-a7-postflight.json").read_text(
                    encoding="utf-8"
                )
            )
            preflight["status"] = "READY"
            preflight["readiness"] = "READY"
            preflight["documentation_consistency"]["status"] = "FAIL"
            (root / "preflight.json").write_text(json.dumps(preflight), encoding="utf-8")
            _write_fixture(root, payload)
            audit = Gate5EvidenceChecker(root).run()
        self.assertIn("PREFLIGHT_READY_CONTRADICTION", {item.code for item in audit.findings})

    def test_ready_session_inventory_rejects_prefilled_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _fixture_payload()
            external = payload["external_evaluation"]
            assert isinstance(external, dict)
            external["status"] = "READY_FOR_SESSION"
            external["results"] = ["result.json"]
            _write_fixture(root, payload)
            (root / "result.json").write_text(json.dumps(_valid_result()), encoding="utf-8")
            audit = Gate5EvidenceChecker(root).run()
        self.assertIn("EXTERNAL_RESULTS", {item.code for item in audit.findings})

    def test_completed_session_loads_and_validates_result_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _fixture_payload()
            external = payload["external_evaluation"]
            assert isinstance(external, dict)
            external["status"] = "COMPLETED"
            external["results"] = ["result.json"]
            external["participant_kit"] = "kit.md"
            external["facilitator_checklist"] = "checklist.md"
            external["preflight"] = "preflight.json"
            _write_fixture(root, payload)
            (root / "result.json").write_text(json.dumps(_valid_result()), encoding="utf-8")
            (root / "kit.md").write_text(
                (ROOT / "docs/evaluations/alpha-python-external-evaluation-participant-kit.md").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            (root / "checklist.md").write_text(
                (
                    ROOT
                    / "docs/evaluations/alpha-python-external-evaluation-facilitator-checklist.md"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (root / "preflight.json").write_text(
                (ROOT / "docs/evaluations/2026-07-18-alpha-python-release-a7-postflight.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            audit = Gate5EvidenceChecker(root).run()
        self.assertTrue(audit.passed, list(audit.findings))

    def test_valid_external_result_contract_is_accepted(self) -> None:
        self.assertEqual(validate_external_result_payload(_valid_result()), ())

    def test_valid_internal_result_contract_is_accepted(self) -> None:
        self.assertEqual(validate_internal_result_payload(_valid_internal_result()), ())

    def test_internal_result_rejects_hidden_independence_and_pii(self) -> None:
        payload = _valid_internal_result()
        payload["email"] = "participant@example.invalid"
        independence = payload["independence"]
        assert isinstance(independence, dict)
        independence["external_to_authoring"] = True
        codes = {item.code for item in validate_internal_result_payload(payload)}
        self.assertIn("INTERNAL_RESULT_FORBIDDEN_KEYS", codes)
        self.assertIn("INTERNAL_RESULT_INDEPENDENCE", codes)

    def test_external_result_rejects_pii_missing_consent_and_incomplete_tasks(self) -> None:
        payload = _valid_result()
        payload["email"] = "participant@example.invalid"
        payload["consent_obtained"] = False
        payload["tasks"] = []
        codes = {item.code for item in validate_external_result_payload(payload)}
        self.assertIn("RESULT_FORBIDDEN_KEYS", codes)
        self.assertIn("RESULT_CONSENT", codes)
        self.assertIn("RESULT_TASK_IDS", codes)

    def test_external_result_rejects_unknown_task_state_and_severity(self) -> None:
        payload = _valid_result()
        tasks = payload["tasks"]
        assert isinstance(tasks, list) and isinstance(tasks[0], dict)
        tasks[0]["state"] = "PASSED"
        payload["findings"] = [{"severity": "URGENT", "state": "OPEN"}]
        codes = {item.code for item in validate_external_result_payload(payload)}
        self.assertIn("RESULT_TASK_STATE", codes)
        self.assertIn("RESULT_FINDING_SEVERITY", codes)

    def test_valid_session_rejects_central_intervention_and_open_high_finding(self) -> None:
        payload = _valid_result()
        tasks = payload["tasks"]
        assert isinstance(tasks, list) and isinstance(tasks[3], dict)
        tasks[3]["state"] = "COMPLETED_WITH_INTERVENTION"
        payload["findings"] = [{"severity": "HIGH", "state": "OPEN"}]
        payload["notes"] = {"company": "must not be collected"}
        codes = {item.code for item in validate_external_result_payload(payload)}
        self.assertIn("RESULT_VALIDITY_TASKS", codes)
        self.assertIn("RESULT_VALIDITY_FINDINGS", codes)
        self.assertIn("RESULT_FORBIDDEN_KEYS", codes)


if __name__ == "__main__":
    unittest.main()
