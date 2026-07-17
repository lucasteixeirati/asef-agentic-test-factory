from __future__ import annotations

import html

from ..report_contracts import AlphaRunReport


class AlphaReportMarkdownRenderer:
    """Render only values already present in a validated AlphaRunReport."""

    def render(self, report: AlphaRunReport) -> str:
        report.validate()
        functional = report.functional_result
        lines = [
            "# ASEF Alpha Run Report",
            "",
            "## Executive summary",
            "",
            f"- Run: `{self._inline(report.run_id)}`",
            f"- Status: `{report.status.value}`",
            f"- Classification: `{report.classification.value}`",
            f"- Terminal: `{str(report.terminal).lower()}`",
            f"- Support level: `{report.support_level.value}`",
            "",
            "## Status and classification",
            "",
            f"- Workflow: `{self._inline(report.workflow_id)}` / `{self._inline(report.workflow_version)}`",
            f"- Execution mode: `{report.execution_mode}`",
            f"- Language profile: `{self._inline(report.language_profile)}`",
            f"- State schema: `{self._inline(report.report_generated_from_state_schema)}`",
            "",
            "## Requirement",
            "",
            f"### {self._text(report.requirement.title)}",
            "",
            self._text(report.requirement.description),
            "",
            "## Analysis and traceability",
            "",
        ]
        lines.extend(
            f"- `{node.node_id}` `{node.kind.value}` — {self._text(node.statement)}"
            for node in report.traceability_nodes
        )
        if report.traceability_links:
            lines.extend(("", "Trace links:", ""))
            lines.extend(
                f"- `{link.source_id}` → `{link.target_id}` (`{link.kind.value}`)"
                for link in report.traceability_links
            )

        lines.extend(("", "## Attempts and functional result", ""))
        if report.attempts:
            lines.extend(
                f"- Attempt `{item.attempt}`: artifact `{item.artifact_id}`, execution "
                f"`{item.generated_execution_id}`, outcome `{item.outcome}`"
                for item in report.attempts
            )
        else:
            lines.append("- No execution attempt is represented in this report.")
        if functional is not None:
            lines.extend(
                (
                    f"- Accepted: `{str(functional.accepted).lower()}`",
                    f"- Conclusion code: `{functional.conclusion_code}`",
                    f"- Tests/passed/failed/errors/skipped: `{self._counter(functional.tests)}` / "
                    f"`{self._counter(functional.passed)}` / `{self._counter(functional.failed)}` / "
                    f"`{self._counter(functional.errors)}` / `{self._counter(functional.skipped)}`",
                )
            )

        lines.extend(("", "## Oracle and human intervention", ""))
        if report.human_interventions:
            lines.extend(
                f"- `{item.intervention_id}`: `{item.kind}` / `{item.decision_code}`"
                for item in report.human_interventions
            )
        else:
            lines.append("- No human intervention is represented in this report.")

        lines.extend(("", "## Quality capabilities", ""))
        lines.extend(
            f"- `{item.capability}`: `{item.status.value}`; complete=`{str(item.complete).lower()}`"
            for item in report.quality
        )

        lines.extend(
            (
                "",
                "## Budgets and usage",
                "",
                f"- Model calls: `{report.usage.model_calls}` / `{report.policy_and_budgets.max_model_calls}`",
                f"- Test corrections: `{report.usage.test_corrections}` / `{report.policy_and_budgets.max_test_corrections}`",
                f"- Input tokens: `{report.usage.input_tokens}` / `{report.policy_and_budgets.max_input_tokens}`",
                f"- Output tokens: `{report.usage.output_tokens}` / `{report.policy_and_budgets.max_output_tokens}`",
                f"- Elapsed milliseconds: `{report.usage.elapsed_ms}`",
                f"- Estimated cost BRL: `{report.usage.estimated_cost_brl}` / `{report.policy_and_budgets.api_budget_brl}`",
                "",
                "## Evidence",
                "",
            )
        )
        lines.extend(
            f"- `{item.evidence_id}`: `{self._inline(item.relative_path)}`; "
            f"integrity=`{item.integrity_status.value}`; publishable=`{str(item.publishable).lower()}`"
            for item in report.evidence
        )

        lines.extend(("", "## Facts", ""))
        lines.extend(
            f"- `{item.fact_id}` `{item.statement_code}` = `{self._inline(str(item.value))}` "
            f"(`{item.observation_status.value}`)"
            for item in report.facts
        )
        lines.extend(("", "## Inferences", ""))
        lines.extend(
            f"- `{item.inference_id}` `{item.conclusion_code}` — {self._text(item.statement)}"
            for item in report.inferences
        )
        lines.extend(("", "## Recommendations", ""))
        if report.recommendations:
            lines.extend(
                f"- `{item.recommendation_code.value}` — {self._text(item.statement)}"
                for item in report.recommendations
            )
        else:
            lines.append("- No recommendation is represented in this report.")
        lines.extend(("", "## Limitations", ""))
        lines.extend(
            f"- `{item.limitation_code}` (`{item.severity.value}`) — {self._text(item.statement)}"
            for item in report.limitations
        )
        lines.extend(
            (
                "",
                "## How to interpret this result",
                "",
                "Use the facts, evidence integrity states, inferences, recommendations, and limitations above as the complete public interpretation represented by this report.",
                "",
            )
        )
        return "\n".join(lines)

    @staticmethod
    def _counter(value: int | None) -> str:
        return "not-observed" if value is None else str(value)

    @staticmethod
    def _inline(value: str) -> str:
        return AlphaReportMarkdownRenderer._text(value).replace("`", "\\`")

    @staticmethod
    def _text(value: str) -> str:
        escaped = html.escape(value, quote=True)
        escaped = escaped.replace("|", "\\|").replace("`", "\\`")
        return " ".join(escaped.splitlines())
