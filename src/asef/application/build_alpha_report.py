from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import PurePosixPath
from typing import Any, Mapping

from ..contracts import ContextSnapshot, SkeletonRunState
from ..outcomes import RunClassification, RunStatus
from ..report_contracts import (
    AlphaRunReport,
    EvidenceIntegrityStatus,
    LimitationSeverity,
    QualityObservationStatus,
    ReportArtifact,
    ReportAttempt,
    ReportEvidence,
    ReportFact,
    ReportFactCategory,
    ReportFactSource,
    ReportFunctionalResult,
    ReportHumanIntervention,
    ReportInference,
    ReportInferenceKind,
    ReportLimitation,
    ReportObservationStatus,
    ReportPolicyAndBudgets,
    ReportQualityObservation,
    ReportRecommendation,
    ReportRecommendationCode,
    ReportRequirement,
    ReportSupportLevel,
    ReportTraceLink,
    ReportTraceNode,
    ReportUsage,
    TraceLinkKind,
    TraceNodeKind,
)


_DISTRIBUTION = "asef-agentic-test-factory"


class BuildAlphaReportService:
    """Compose the normative public report without filesystem or presentation access."""

    def build(
        self,
        state: SkeletonRunState,
        snapshot: ContextSnapshot,
        evaluation: Mapping[str, object],
        evidence: tuple[ReportEvidence, ...],
    ) -> AlphaRunReport:
        state.validate()
        snapshot.validate()
        if not evidence:
            raise ValueError("Alpha report requires verified evidence observations")

        evidence_by_path = {item.relative_path: item.evidence_id for item in evidence}
        default_evidence = (evidence[0].evidence_id,)
        nodes, links = self._traceability(state, evidence_by_path)
        artifacts = self._artifacts(state, evidence_by_path)
        attempts = self._attempts(state, artifacts, evidence, nodes, links)
        limitations = self._limitations(state, evidence)
        facts = self._facts(state, evaluation, evidence_by_path)
        quality, quality_facts, quality_limitations = self._quality(
            state, evidence, len(limitations)
        )
        facts += quality_facts
        limitations += quality_limitations
        functional = self._functional(state, evaluation, default_evidence)
        inference = ReportInference(
            "INF-FUNCTIONAL-RESULT",
            ReportInferenceKind.FUNCTIONAL_RESULT,
            functional.conclusion_code,
            self._functional_statement(state.classification),
            ("FACT-FUNCTIONAL-ACCEPTED",),
            functional.evidence_ids,
            None if functional.accepted else "The result is bounded to the recorded evidence",
        )
        recommendations = self._recommendations(state.classification, inference, limitations)

        report = AlphaRunReport(
            report_id=state.run_id,
            asef_version=self._asef_version(),
            run_id=state.run_id,
            workflow_id=state.workflow_id,
            workflow_version=state.workflow_version,
            status=state.status,
            classification=state.classification,
            terminal=self._terminal(state.status),
            execution_mode=state.request.execution_mode,
            language_profile=snapshot.language_profile,
            support_level=ReportSupportLevel.EXPERIMENTAL,
            context_snapshot_ref=state.context_snapshot_ref or "context-snapshot.json",
            report_generated_from_state_schema=state.schema_version,
            requirement=ReportRequirement(
                "REQ-001",
                state.request.requirement_title,
                state.request.requirement_description,
            ),
            traceability_nodes=tuple(nodes),
            traceability_links=tuple(links),
            artifacts=tuple(artifacts),
            attempts=tuple(attempts),
            functional_result=functional,
            quality=quality,
            human_interventions=self._human_interventions(state, default_evidence),
            policy_and_budgets=ReportPolicyAndBudgets(
                state.budgets.max_model_calls,
                state.budgets.max_test_corrections,
                state.budgets.max_input_tokens,
                state.budgets.max_output_tokens,
                state.budgets.max_workflow_seconds,
                state.budgets.api_budget_brl,
            ),
            usage=ReportUsage(
                state.usage.model_calls,
                state.usage.provider_retries,
                state.usage.test_corrections,
                state.usage.input_tokens,
                state.usage.output_tokens,
                state.usage.elapsed_ms,
                state.usage.estimated_cost_brl,
            ),
            evidence=evidence,
            facts=facts,
            inferences=(inference,),
            recommendations=recommendations,
            limitations=limitations,
        )
        report.validate()
        return report

    @staticmethod
    def _traceability(
        state: SkeletonRunState, evidence_by_path: Mapping[str, str]
    ) -> tuple[list[ReportTraceNode], list[ReportTraceLink]]:
        nodes = [
            ReportTraceNode(
                "REQ-001",
                TraceNodeKind.REQUIREMENT,
                state.request.requirement_description,
            )
        ]
        links: list[ReportTraceLink] = []
        analysis = state.facts.get("analysis")
        if isinstance(analysis, Mapping):
            for key, prefix, kind in (
                ("behaviors", "BEH", TraceNodeKind.BEHAVIOR),
                ("risks", "RSK", TraceNodeKind.RISK),
                ("scenarios", "SCN", TraceNodeKind.SCENARIO),
            ):
                values = analysis.get(key, [])
                if isinstance(values, list):
                    for index, statement in enumerate(values, 1):
                        node_id = f"{prefix}-{index:03d}"
                        nodes.append(ReportTraceNode(node_id, kind, str(statement)))
                        links.append(
                            ReportTraceLink(
                                "REQ-001",
                                node_id,
                                TraceLinkKind.DERIVED_FROM_REQUIREMENT,
                            )
                        )

        artifact = state.facts.get("artifact")
        if isinstance(artifact, Mapping):
            path = str(artifact.get("relative_path", ""))
            attempt = BuildAlphaReportService._artifact_attempt(path)
            artifact_id = f"ART-ATTEMPT-{attempt:03d}"
            artifact_evidence = evidence_by_path.get(path)
            nodes.append(
                ReportTraceNode(
                    artifact_id,
                    TraceNodeKind.ARTIFACT,
                    "Generated unit test artifact",
                    (artifact_evidence,) if artifact_evidence else (),
                )
            )
            scenario_ids = artifact.get("scenario_ids", [])
            if isinstance(scenario_ids, list):
                for scenario_id in scenario_ids:
                    links.append(
                        ReportTraceLink(
                            artifact_id,
                            str(scenario_id),
                            TraceLinkKind.COVERS_SCENARIO,
                        )
                    )
            if state.status is RunStatus.SUCCEEDED or "execution" in state.facts or "latest_evaluation" in state.facts:
                execution_id = f"EXEC-ATTEMPT-{attempt:03d}-generated"
                execution_evidence = tuple(
                    item[1]
                    for item in evidence_by_path_to_items(evidence_by_path)
                    if BuildAlphaReportService._is_execution_path(item[0])
                )
                nodes.append(
                    ReportTraceNode(
                        execution_id,
                        TraceNodeKind.EXECUTION,
                        "Generated test execution",
                        execution_evidence,
                    )
                )
                links.append(
                    ReportTraceLink(
                        execution_id,
                        artifact_id,
                        TraceLinkKind.EXECUTES_ARTIFACT,
                    )
                )
        return nodes, links

    @staticmethod
    def _artifacts(
        state: SkeletonRunState, evidence_by_path: Mapping[str, str]
    ) -> list[ReportArtifact]:
        value = state.facts.get("artifact")
        if not isinstance(value, Mapping):
            return []
        path = str(value.get("relative_path", ""))
        evidence_id = evidence_by_path.get(path)
        scenario_ids = value.get("scenario_ids", [])
        if not evidence_id or not isinstance(scenario_ids, list):
            return []
        attempt = BuildAlphaReportService._artifact_attempt(path)
        return [
            ReportArtifact(
                f"ART-ATTEMPT-{attempt:03d}",
                path,
                str(value.get("sha256", "")),
                tuple(str(item) for item in scenario_ids),
                attempt,
                (evidence_id,),
            )
        ]

    @staticmethod
    def _attempts(
        state: SkeletonRunState,
        artifacts: list[ReportArtifact],
        evidence: tuple[ReportEvidence, ...],
        nodes: list[ReportTraceNode],
        links: list[ReportTraceLink],
    ) -> list[ReportAttempt]:
        del nodes, links
        if not artifacts or not (
            state.status is RunStatus.SUCCEEDED
            or "execution" in state.facts
            or "latest_evaluation" in state.facts
        ):
            return []
        artifact = artifacts[0]
        refs = tuple(
            item.evidence_id
            for item in evidence
            if BuildAlphaReportService._is_execution_path(item.relative_path)
        ) or artifact.evidence_ids
        outcome = "PASSED" if state.status is RunStatus.SUCCEEDED else "NOT_ACCEPTED"
        return [
            ReportAttempt(
                artifact.attempt,
                artifact.artifact_id,
                f"EXEC-ATTEMPT-{artifact.attempt:03d}-generated",
                None,
                outcome,
                refs,
            )
        ]

    @staticmethod
    def _facts(
        state: SkeletonRunState,
        evaluation: Mapping[str, object],
        evidence_by_path: Mapping[str, str],
    ) -> tuple[ReportFact, ...]:
        execution_path = next(
            (path for path in evidence_by_path if BuildAlphaReportService._is_execution_path(path)),
            None,
        )
        execution_evidence = (
            (evidence_by_path[execution_path],) if execution_path is not None else ()
        )
        return (
            ReportFact(
                "FACT-STATUS",
                ReportFactCategory.EXECUTION,
                "RUN_STATUS",
                state.status.value,
                ReportFactSource.STATE,
                ReportObservationStatus.OBSERVED,
            ),
            ReportFact(
                "FACT-CLASSIFICATION",
                ReportFactCategory.ORACLE,
                "RUN_CLASSIFICATION",
                state.classification.value,
                ReportFactSource.EVALUATION,
                ReportObservationStatus.OBSERVED,
                evidence_ids=execution_evidence,
            ),
            ReportFact(
                "FACT-FUNCTIONAL-ACCEPTED",
                ReportFactCategory.ORACLE,
                "FUNCTIONAL_ACCEPTED",
                state.status is RunStatus.SUCCEEDED
                and state.classification is RunClassification.ACCEPTED,
                ReportFactSource.EVALUATION,
                ReportObservationStatus.OBSERVED,
                evidence_ids=execution_evidence,
            ),
        )

    @staticmethod
    def _functional(
        state: SkeletonRunState,
        evaluation: Mapping[str, object],
        default_evidence: tuple[str, ...],
    ) -> ReportFunctionalResult:
        accepted = (
            state.status is RunStatus.SUCCEEDED
            and state.classification is RunClassification.ACCEPTED
        )

        def counter(name: str) -> int | None:
            value = evaluation.get(name)
            return value if isinstance(value, int) and not isinstance(value, bool) else None

        tests = counter("tests")
        passed = counter("passed")
        failed = counter("failed")
        errors = counter("errors")
        skipped = counter("skipped")
        if accepted:
            errors = 0 if errors is None else errors
            skipped = 0 if skipped is None else skipped
            failed = 0 if failed is None else failed
        return ReportFunctionalResult(
            accepted,
            BuildAlphaReportService._conclusion_code(state.classification),
            tests,
            passed,
            failed,
            errors,
            skipped,
            ("INF-FUNCTIONAL-RESULT",),
            default_evidence,
        )

    @staticmethod
    def _quality(
        state: SkeletonRunState,
        evidence: tuple[ReportEvidence, ...],
        limitation_offset: int,
    ) -> tuple[
        tuple[ReportQualityObservation, ...],
        tuple[ReportFact, ...],
        tuple[ReportLimitation, ...],
    ]:
        value = state.facts.get("quality")
        if not isinstance(value, Mapping):
            return (
                (
                    ReportQualityObservation(
                        "quality",
                        QualityObservationStatus.NOT_REQUESTED,
                        False,
                        (),
                        (),
                        ("QUALITY_NOT_REQUESTED",),
                    ),
                ),
                (),
                (),
            )
        observations = value.get("observations", [])
        if not isinstance(observations, list) or not observations:
            return (), (), ()
        quality_evidence = tuple(
            item.evidence_id
            for item in evidence
            if "quality" in item.kind.lower() or "quality" in item.relative_path.lower()
        ) or (evidence[0].evidence_id,)
        result: list[ReportQualityObservation] = []
        facts: list[ReportFact] = []
        limitations: list[ReportLimitation] = []
        for index, observation in enumerate(observations, 1):
            if not isinstance(observation, Mapping):
                continue
            capability = str(observation.get("capability", f"quality-{index}"))
            raw_status = str(observation.get("status", "FAILED"))
            try:
                status = QualityObservationStatus(raw_status)
            except ValueError:
                status = QualityObservationStatus.FAILED
            complete = status is QualityObservationStatus.COMPLETED
            fact_id = f"FACT-QUALITY-{index:03d}"
            facts.append(
                ReportFact(
                    fact_id,
                    ReportFactCategory.QUALITY,
                    "QUALITY_CAPABILITY_STATUS",
                    status.value,
                    ReportFactSource.QUALITY,
                    ReportObservationStatus.OBSERVED,
                    evidence_ids=quality_evidence,
                )
            )
            limitation_codes: tuple[str, ...] = ()
            if not complete:
                code = f"QUALITY_{limitation_offset + index:03d}_INCOMPLETE"
                limitation_codes = (code,)
                limitations.append(
                    ReportLimitation(
                        code,
                        LimitationSeverity.WARNING,
                        f"Quality capability {capability} did not complete",
                    )
                )
            result.append(
                ReportQualityObservation(
                    capability,
                    status,
                    complete,
                    (fact_id,),
                    quality_evidence,
                    limitation_codes,
                )
            )
        return tuple(result), tuple(facts), tuple(limitations)

    @staticmethod
    def _limitations(
        state: SkeletonRunState, evidence: tuple[ReportEvidence, ...]
    ) -> tuple[ReportLimitation, ...]:
        values = [
            ReportLimitation(
                "REFERENCE_PROFILE_ONLY",
                LimitationSeverity.INFO,
                "The result applies only to the bounded Python reference profile",
            ),
            ReportLimitation(
                "NOT_SAFE_FOR_PRODUCTION",
                LimitationSeverity.WARNING,
                "The experimental runtime is not approved for production workloads",
            ),
        ]
        if not isinstance(state.facts.get("quality"), Mapping):
            values.append(
                ReportLimitation(
                    "QUALITY_NOT_REQUESTED",
                    LimitationSeverity.INFO,
                    "Quality capabilities were not requested for this run",
                )
            )
        else:
            values.append(
                ReportLimitation(
                    "QUALITY_EVIDENCE_ONLY",
                    LimitationSeverity.INFO,
                    "Quality signals are evidence only; no universal threshold is applied",
                )
            )
        if any(
            item.integrity_status
            in {EvidenceIntegrityStatus.MISSING, EvidenceIntegrityStatus.MISMATCH}
            for item in evidence
        ):
            values.append(
                ReportLimitation(
                    "EVIDENCE_INTEGRITY_FAILURE",
                    LimitationSeverity.BLOCKING,
                    "One or more evidence references could not be verified",
                )
            )
        return tuple(values)

    @staticmethod
    def _recommendations(
        classification: RunClassification,
        inference: ReportInference,
        limitations: tuple[ReportLimitation, ...],
    ) -> tuple[ReportRecommendation, ...]:
        mapping = {
            RunClassification.SUT_DEFECT_SUSPECTED: (
                ReportRecommendationCode.REVIEW_SUT_DEFECT,
                "Review the evidence-backed SUT defect suspicion",
            ),
            RunClassification.TEST_FAILURE: (
                ReportRecommendationCode.REVIEW_GENERATED_TEST,
                "Review the generated test and its execution evidence",
            ),
            RunClassification.TEST_ERROR: (
                ReportRecommendationCode.REVIEW_GENERATED_TEST,
                "Review the generated test error and normalized evidence",
            ),
            RunClassification.INFRASTRUCTURE_ERROR: (
                ReportRecommendationCode.RUN_ASEF_DOCTOR,
                "Run asef doctor before retrying the workflow",
            ),
            RunClassification.POLICY_VIOLATION: (
                ReportRecommendationCode.REVIEW_POLICY,
                "Review the policy finding before changing the input",
            ),
            RunClassification.BUDGET_ERROR: (
                ReportRecommendationCode.REVIEW_BUDGET,
                "Review the explicit budget before deciding whether to retry",
            ),
            RunClassification.WAITING_HUMAN: (
                ReportRecommendationCode.PROVIDE_CLARIFICATION,
                "Provide the requested clarification through the resume command",
            ),
        }
        selected = mapping.get(classification)
        recommendations: list[ReportRecommendation] = []
        if selected is not None:
            recommendations.append(
                ReportRecommendation(
                    "REC-NEXT-ACTION",
                    selected[0],
                    inference.inference_id,
                    selected[1],
                    classification
                    in {
                        RunClassification.INFRASTRUCTURE_ERROR,
                        RunClassification.POLICY_VIOLATION,
                        RunClassification.BUDGET_ERROR,
                    },
                    (inference.inference_id,),
                )
            )
        recommendations.append(
            ReportRecommendation(
                "REC-NOT-PRODUCTION",
                ReportRecommendationCode.DO_NOT_USE_IN_PRODUCTION,
                "NOT_SAFE_FOR_PRODUCTION",
                "Do not use this experimental result as production approval",
                False,
                (),
                ("NOT_SAFE_FOR_PRODUCTION",),
            )
        )
        return tuple(recommendations)

    @staticmethod
    def _human_interventions(
        state: SkeletonRunState, evidence_ids: tuple[str, ...]
    ) -> tuple[ReportHumanIntervention, ...]:
        values: list[ReportHumanIntervention] = []
        decisions = state.facts.get("human_decisions")
        if isinstance(decisions, list):
            for index, decision in enumerate(decisions, 1):
                if not isinstance(decision, Mapping):
                    continue
                action = str(decision.get("action", "DECISION")).upper()
                action = "".join(char if char.isalnum() else "_" for char in action)
                values.append(
                    ReportHumanIntervention(
                        f"HUMAN-{index:03d}",
                        "HUMAN_DECISION",
                        action,
                        evidence_ids,
                    )
                )
        review = state.facts.get("sut_defect_review")
        if isinstance(review, Mapping):
            decision = str(review.get("decision", "REVIEWED")).upper()
            decision = "".join(char if char.isalnum() else "_" for char in decision)
            values.append(
                ReportHumanIntervention(
                    f"HUMAN-{len(values) + 1:03d}",
                    "SUT_DEFECT_REVIEW",
                    decision,
                    evidence_ids,
                )
            )
        return tuple(values)

    @staticmethod
    def _artifact_attempt(path: str) -> int:
        for part in PurePosixPath(path).parts:
            if part.startswith("attempt-") and part[8:].isdigit():
                return max(1, int(part[8:]))
        return 1

    @staticmethod
    def _is_execution_path(path: str) -> bool:
        lowered = path.lower()
        return any(marker in lowered for marker in ("execution", "stdout", "stderr", "junit"))

    @staticmethod
    def _conclusion_code(classification: RunClassification) -> str:
        return {
            RunClassification.ACCEPTED: "GENERATED_TESTS_ACCEPTED",
            RunClassification.CANCELLED_BY_USER: "RUN_CANCELLED_BY_USER",
            RunClassification.POLICY_VIOLATION: "RUN_BLOCKED_BY_POLICY",
            RunClassification.BUDGET_ERROR: "RUN_BUDGET_EXHAUSTED",
            RunClassification.INFRASTRUCTURE_ERROR: "RUN_INFRASTRUCTURE_FAILED",
            RunClassification.TEST_ERROR: "GENERATED_TEST_ERROR",
            RunClassification.TEST_FAILURE: "GENERATED_TESTS_REJECTED",
            RunClassification.SUT_DEFECT_SUSPECTED: "SUT_DEFECT_SUSPECTED",
            RunClassification.INCONCLUSIVE: "RUN_INCONCLUSIVE",
        }.get(classification, "RUN_NOT_ACCEPTED")

    @staticmethod
    def _functional_statement(classification: RunClassification) -> str:
        if classification is RunClassification.ACCEPTED:
            return "The generated tests satisfied the deterministic acceptance rule"
        return f"The terminal run was classified as {classification.value}"

    @staticmethod
    def _terminal(status: RunStatus) -> bool:
        return status in {
            RunStatus.SUCCEEDED,
            RunStatus.FAILED,
            RunStatus.CANCELLED,
            RunStatus.POLICY_BLOCKED,
            RunStatus.BUDGET_EXHAUSTED,
        }

    @staticmethod
    def _asef_version() -> str:
        try:
            return version(_DISTRIBUTION)
        except PackageNotFoundError:
            return "0.1.0a7"


def evidence_by_path_to_items(value: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(value.items())
