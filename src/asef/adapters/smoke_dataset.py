from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..contracts import ContractValidationError, SkeletonRunRequest
from ..evaluation_contracts import DatasetCase, DatasetKind, dataset_case_from_dict
from ..outcomes import RunStatus
from ..smoke_contracts import (
    SMOKE_CASE_IDS,
    LoadedSmokeCase,
    LoadedSmokeDataset,
    SmokeDemoSpec,
    smoke_demo_spec_from_dict,
)
from .context_file import FileQualityContextAdapter


MAX_SMOKE_JSON_BYTES = 256 * 1024
MAX_SMOKE_TEXT_BYTES = 64 * 1024
MAX_SMOKE_TOTAL_BYTES = 4 * 1024 * 1024


class SmokeDatasetLoader:
    """Load and validate the complete public Smoke dataset without side effects."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def load(self, dataset_root: str | Path) -> LoadedSmokeDataset:
        root = self._inside_workspace(Path(dataset_root), "dataset root")
        if not root.is_dir():
            raise ContractValidationError("smoke dataset root does not exist")

        directories: dict[str, Path] = {}
        for item in root.iterdir():
            if item.name.startswith("SMK-") and not item.is_dir():
                raise ContractValidationError(
                    f"smoke case entry must be a directory: {item.name}"
                )
            if item.is_dir() and item.name.startswith("SMK-"):
                resolved = self._inside_workspace(item, f"dataset case {item.name}")
                if item.name in directories:
                    raise ContractValidationError(f"duplicate smoke case directory: {item.name}")
                directories[item.name] = resolved
        found = set(directories)
        expected = set(SMOKE_CASE_IDS)
        if found != expected:
            missing = sorted(expected - found)
            extra = sorted(found - expected)
            raise ContractValidationError(
                f"smoke dataset must contain exactly SMK-001 through SMK-010; "
                f"missing={missing}, extra={extra}"
            )

        loaded_files: dict[str, bytes] = {}
        loaded_cases: list[LoadedSmokeCase] = []
        for case_id in SMOKE_CASE_IDS:
            directory = directories[case_id]
            case_path = self._inside_workspace(directory / "case.json", f"{case_id} case.json")
            demo_path = self._inside_workspace(directory / "demo.json", f"{case_id} demo.json")
            case = dataset_case_from_dict(
                self._read_json(case_path, loaded_files, MAX_SMOKE_JSON_BYTES)
            )
            demo = smoke_demo_spec_from_dict(
                self._read_json(demo_path, loaded_files, MAX_SMOKE_JSON_BYTES)
            )
            self._validate_pair(case_id, case, demo)
            self._validate_refs(case, demo, loaded_files)
            loaded_cases.append(
                LoadedSmokeCase(
                    case=case,
                    demo=demo,
                    directory_ref=directory.relative_to(self.workspace_root).as_posix(),
                )
            )

        loaded_bytes = sum(len(content) for content in loaded_files.values())
        if loaded_bytes > MAX_SMOKE_TOTAL_BYTES:
            raise ContractValidationError(
                f"smoke dataset exceeds {MAX_SMOKE_TOTAL_BYTES} loaded bytes"
            )
        digest = hashlib.sha256()
        for ref, content in sorted(loaded_files.items()):
            encoded_ref = ref.encode("utf-8")
            digest.update(len(encoded_ref).to_bytes(4, "big"))
            digest.update(encoded_ref)
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
        return LoadedSmokeDataset(
            root_ref=root.relative_to(self.workspace_root).as_posix(),
            cases=tuple(loaded_cases),
            dataset_hash=digest.hexdigest(),
            loaded_bytes=loaded_bytes,
        )

    def read_text_ref(self, ref: str) -> str:
        path = self._inside_workspace(Path(ref), f"smoke text ref {ref}")
        if not path.is_file() or path.stat().st_size > MAX_SMOKE_TEXT_BYTES:
            raise ContractValidationError("smoke text ref is missing or exceeds its size limit")
        try:
            value = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise ContractValidationError("smoke text ref is not valid UTF-8") from exc
        if not value.strip():
            raise ContractValidationError("smoke text ref cannot be empty")
        return value

    def normalize_ref(self, ref: str | Path) -> str:
        return self._inside_workspace(Path(ref), f"smoke ref {ref}").relative_to(
            self.workspace_root
        ).as_posix()

    def _validate_pair(
        self,
        directory_id: str,
        case: DatasetCase,
        demo: SmokeDemoSpec,
    ) -> None:
        if case.kind is not DatasetKind.SMOKE:
            raise ContractValidationError(f"{directory_id} is not a SMOKE dataset case")
        if case.case_id != directory_id or demo.case_id != directory_id:
            raise ContractValidationError(
                f"smoke directory, case.json and demo.json IDs differ for {directory_id}"
            )
        if demo.case_version != case.version:
            raise ContractValidationError(f"smoke case and demo versions differ for {directory_id}")
        if "demo" not in case.allowed_modes:
            raise ContractValidationError(f"{directory_id} does not allow demo mode")
        if demo.expected.classification.value not in case.expected_classifications:
            raise ContractValidationError(
                f"{directory_id} terminal classification is not allowed by case.json"
            )
        if demo.expected.oracle_executed and not case.oracle_ref:
            raise ContractValidationError(
                f"{directory_id} cannot execute an oracle absent from case.json"
            )
        if case.oracle_ref and not demo.expected.oracle_executed and demo.expected.status not in {
            # An oracle can exist but remain intentionally unreachable.
            RunStatus.WAITING_FOR_CLARIFICATION,
            RunStatus.POLICY_BLOCKED,
            RunStatus.BUDGET_EXHAUSTED,
            RunStatus.FAILED,
        }:
            raise ContractValidationError(
                f"{directory_id} oracle expectation is inconsistent with case.json"
            )

    def _validate_refs(
        self,
        case: DatasetCase,
        demo: SmokeDemoSpec,
        loaded_files: dict[str, bytes],
    ) -> None:
        self._require_directory(case.sut_ref)
        file_refs = {
            case.requirement_ref,
            *case.generation_input_refs,
            *case.evaluation_input_refs,
            demo.context_ref,
            demo.analysis_cassette_ref,
            *demo.artifact_cassette_refs,
        }
        if case.oracle_ref:
            file_refs.add(case.oracle_ref)
        for ref in sorted(file_refs):
            limit = MAX_SMOKE_JSON_BYTES if ref.endswith(".json") else MAX_SMOKE_TEXT_BYTES
            self._read_file_ref(ref, loaded_files, limit)

        self._validate_context(case, demo, loaded_files)

        generation_refs = {
            *case.generation_input_refs,
            demo.analysis_cassette_ref,
            *demo.artifact_cassette_refs,
        }
        if case.oracle_ref and case.oracle_ref in generation_refs:
            raise ContractValidationError(f"{case.case_id} exposes its oracle to generation")
        if case.oracle_ref:
            for cassette_ref in (demo.analysis_cassette_ref, *demo.artifact_cassette_refs):
                value = self._decode_json(loaded_files[cassette_ref], cassette_ref)
                if self._contains_exact_value(value, case.oracle_ref):
                    raise ContractValidationError(
                        f"{case.case_id} cassette exposes its oracle to generation"
                    )
        analysis = self._decode_json(
            loaded_files[demo.analysis_cassette_ref], demo.analysis_cassette_ref
        )
        self._require_cassette_schema(analysis, {"wf001_analysis"}, demo.analysis_cassette_ref)
        for index, cassette_ref in enumerate(demo.artifact_cassette_refs):
            cassette = self._decode_json(loaded_files[cassette_ref], cassette_ref)
            schemas = {"wf001_unit_artifact"}
            if index > 0:
                schemas.add("wf001_unit_correction")
            self._require_cassette_schema(cassette, schemas, cassette_ref)

    def _validate_context(
        self,
        case: DatasetCase,
        demo: SmokeDemoSpec,
        loaded_files: dict[str, bytes],
    ) -> None:
        request = SkeletonRunRequest(
            context_ref=demo.context_ref,
            system_id=demo.system_id,
            requested_skill="unit",
            requirement_title=case.title,
            requirement_description="Validate the versioned Smoke Dataset context.",
            execution_mode="demo",
        )
        try:
            resolved = FileQualityContextAdapter(self.workspace_root).resolve(request)
        except (OSError, ValueError) as exc:
            raise ContractValidationError(
                f"{case.case_id} cannot resolve its declared context: {exc}"
            ) from exc
        if resolved.snapshot.provider != "recorded" or resolved.snapshot.mode != "demo":
            raise ContractValidationError(
                f"{case.case_id} smoke context must resolve to recorded demo mode"
            )
        case_sut = self._inside_workspace(Path(case.sut_ref), f"{case.case_id} SUT")
        if not resolved.authorized_root.is_relative_to(case_sut):
            raise ContractValidationError(
                f"{case.case_id} context repository does not belong to its declared SUT"
            )
        authorized_refs: set[str] = set()
        for relative in resolved.authorized_files:
            path = self._inside_workspace(
                resolved.authorized_root / relative,
                f"{case.case_id} authorized source",
            )
            ref = path.relative_to(self.workspace_root).as_posix()
            authorized_refs.add(ref)
            self._read_file(path, loaded_files, MAX_SMOKE_TEXT_BYTES)
        sut_generation_refs = {
            ref
            for ref in case.generation_input_refs
            if self._inside_workspace(Path(ref), f"{case.case_id} generation ref").is_relative_to(
                case_sut
            )
        }
        if not sut_generation_refs.issubset(authorized_refs):
            raise ContractValidationError(
                f"{case.case_id} generation source is outside the context read_scope"
            )

    def _require_directory(self, ref: str) -> None:
        path = self._inside_workspace(Path(ref), f"smoke ref {ref}")
        if not path.is_dir():
            raise ContractValidationError(f"smoke directory ref does not exist: {ref}")

    def _read_file_ref(
        self,
        ref: str,
        loaded_files: dict[str, bytes],
        limit: int,
    ) -> bytes:
        if ref in loaded_files:
            return loaded_files[ref]
        path = self._inside_workspace(Path(ref), f"smoke ref {ref}")
        return self._read_file(path, loaded_files, limit)

    def _read_json(
        self,
        path: Path,
        loaded_files: dict[str, bytes],
        limit: int,
    ) -> dict[str, Any]:
        content = self._read_file(path, loaded_files, limit)
        value = self._decode_json(content, path.as_posix())
        if not isinstance(value, dict):
            raise ContractValidationError(f"smoke JSON must contain an object: {path.name}")
        return value

    def _read_file(
        self,
        path: Path,
        loaded_files: dict[str, bytes],
        limit: int,
    ) -> bytes:
        if not path.is_file():
            raise ContractValidationError(f"smoke file ref does not exist: {path.name}")
        ref = path.relative_to(self.workspace_root).as_posix()
        if ref in loaded_files:
            return loaded_files[ref]
        size = path.stat().st_size
        if size > limit:
            raise ContractValidationError(f"smoke file exceeds {limit} bytes: {ref}")
        content = path.read_bytes()
        loaded_files[ref] = content
        if sum(len(item) for item in loaded_files.values()) > MAX_SMOKE_TOTAL_BYTES:
            raise ContractValidationError(
                f"smoke dataset exceeds {MAX_SMOKE_TOTAL_BYTES} loaded bytes"
            )
        return content

    def _decode_json(self, content: bytes, ref: str) -> Any:
        try:
            return json.loads(
                content.decode("utf-8"),
                object_pairs_hook=self._unique_object,
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ContractValidationError(f"invalid smoke JSON {ref}: {exc}") from exc

    @staticmethod
    def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContractValidationError(f"duplicate JSON field: {key}")
            result[key] = value
        return result

    @staticmethod
    def _contains_exact_value(value: Any, expected: str) -> bool:
        if value == expected:
            return True
        if isinstance(value, dict):
            return any(
                SmokeDatasetLoader._contains_exact_value(item, expected)
                for item in value.values()
            )
        if isinstance(value, list):
            return any(
                SmokeDatasetLoader._contains_exact_value(item, expected) for item in value
            )
        return False

    @staticmethod
    def _require_cassette_schema(value: Any, schemas: set[str], ref: str) -> None:
        if (
            not isinstance(value, dict)
            or value.get("schema_name") not in schemas
            or not isinstance(value.get("output"), dict)
        ):
            raise ContractValidationError(
                f"smoke cassette has an invalid schema or output: {ref}"
            )

    def _inside_workspace(self, path: Path, label: str) -> Path:
        candidate = (self.workspace_root / path).resolve() if not path.is_absolute() else path.resolve()
        if not candidate.is_relative_to(self.workspace_root):
            raise ContractValidationError(f"{label} escapes the ASEF workspace")
        return candidate
