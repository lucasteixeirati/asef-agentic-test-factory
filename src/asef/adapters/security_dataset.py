from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..contracts import ContractValidationError
from ..security_contracts import (
    SECURITY_CASE_IDS,
    LoadedSecurityCase,
    LoadedSecurityDataset,
    security_case_spec_from_dict,
)


MAX_SECURITY_FILE_BYTES = 64 * 1024
MAX_SECURITY_TOTAL_BYTES = 2 * 1024 * 1024
_MANIFEST_FIELDS = {"schema_version", "dataset_id", "version", "case_ids", "limitations"}


class SecurityDatasetLoader:
    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def load(self, dataset_root: str | Path) -> LoadedSecurityDataset:
        root = self._inside_workspace(Path(dataset_root), "security dataset root")
        if not root.is_dir() or root.is_symlink() or self._is_junction(root):
            raise ContractValidationError("security dataset root must be a real directory")
        entries = {item.name: item for item in root.iterdir()}
        allowed_root = {"manifest.json", *SECURITY_CASE_IDS}
        if set(entries) != allowed_root:
            raise ContractValidationError("security dataset root contains an unexpected fileset")

        loaded: dict[str, bytes] = {}
        manifest = self._read_json(entries["manifest.json"], loaded)
        extras = set(manifest) - _MANIFEST_FIELDS
        if extras:
            raise ContractValidationError(
                f"security manifest contains unknown fields: {sorted(extras)}"
            )
        try:
            if (
                manifest["schema_version"] != "1.0.0"
                or manifest["dataset_id"] != "asef-security"
                or tuple(manifest["case_ids"]) != SECURITY_CASE_IDS
                or not isinstance(manifest["version"], str)
                or not isinstance(manifest["limitations"], list)
                or not manifest["limitations"]
                or any(
                    not isinstance(item, str)
                    or not item.strip()
                    or len(item) > 500
                    for item in manifest["limitations"]
                )
            ):
                raise ContractValidationError("security manifest identity is invalid")
        except (KeyError, TypeError) as exc:
            raise ContractValidationError("security manifest is incomplete") from exc

        cases: list[LoadedSecurityCase] = []
        for case_id in SECURITY_CASE_IDS:
            directory = self._inside_workspace(entries[case_id], case_id)
            if not directory.is_dir() or directory.is_symlink() or self._is_junction(directory):
                raise ContractValidationError(f"{case_id} must be a real directory")
            case_entries = {item.name: item for item in directory.iterdir()}
            if set(case_entries) != {"case.json", "README.md", "fixtures"}:
                raise ContractValidationError(f"{case_id} contains an unexpected fileset")
            fixtures = case_entries["fixtures"]
            if not fixtures.is_dir() or fixtures.is_symlink() or self._is_junction(fixtures):
                raise ContractValidationError(f"{case_id} fixtures must be a real directory")
            fixture_entries = list(fixtures.iterdir())
            if len(fixture_entries) != 1 or fixture_entries[0].name != "fixture.txt":
                raise ContractValidationError(f"{case_id} fixtures fileset is invalid")
            spec = security_case_spec_from_dict(
                self._read_json(case_entries["case.json"], loaded)
            )
            if spec.case_id != case_id:
                raise ContractValidationError(f"{case_id} directory and case identity differ")
            expected_fixture = f"datasets/security/{case_id}/fixtures/fixture.txt"
            if spec.fixture_refs != (expected_fixture,):
                raise ContractValidationError(f"{case_id} fixture refs are not canonical")
            self._read_file(case_entries["README.md"], loaded)
            self._read_file(fixture_entries[0], loaded)
            cases.append(
                LoadedSecurityCase(
                    spec=spec,
                    directory_ref=directory.relative_to(self.workspace_root).as_posix(),
                )
            )

        digest = hashlib.sha256()
        for ref, content in sorted(loaded.items()):
            encoded = ref.encode("utf-8")
            digest.update(len(encoded).to_bytes(4, "big"))
            digest.update(encoded)
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
        return LoadedSecurityDataset(
            root_ref=root.relative_to(self.workspace_root).as_posix(),
            version=str(manifest["version"]),
            cases=tuple(cases),
            dataset_hash=digest.hexdigest(),
            loaded_bytes=sum(len(item) for item in loaded.values()),
        )

    def read_fixture(self, ref: str) -> str:
        path = self._inside_workspace(Path(ref), "security fixture")
        content: dict[str, bytes] = {}
        return self._read_file(path, content).decode("utf-8")

    def _read_json(self, path: Path, loaded: dict[str, bytes]) -> dict[str, Any]:
        content = self._read_file(path, loaded)
        try:
            value = json.loads(
                content.decode("utf-8"),
                object_pairs_hook=self._unique_object,
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ContractValidationError(f"invalid security JSON: {path.name}") from exc
        if not isinstance(value, dict):
            raise ContractValidationError("security JSON must contain an object")
        return value

    def _read_file(self, path: Path, loaded: dict[str, bytes]) -> bytes:
        resolved = self._inside_workspace(path, "security file")
        if (
            not resolved.is_file()
            or resolved.is_symlink()
            or self._is_junction(resolved)
            or resolved.stat().st_size > MAX_SECURITY_FILE_BYTES
        ):
            raise ContractValidationError("security file is missing, linked or oversized")
        ref = resolved.relative_to(self.workspace_root).as_posix()
        content = resolved.read_bytes()
        if resolved.suffix.lower() in {".md", ".txt"}:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ContractValidationError("security text file must be UTF-8") from exc
            if not text.strip():
                raise ContractValidationError("security text file cannot be empty")
        loaded[ref] = content
        if sum(len(item) for item in loaded.values()) > MAX_SECURITY_TOTAL_BYTES:
            raise ContractValidationError("security dataset exceeds its total byte limit")
        return content

    def _inside_workspace(self, path: Path, label: str) -> Path:
        raw = self.workspace_root / path if not path.is_absolute() else path
        absolute = raw.absolute()
        try:
            relative = absolute.relative_to(self.workspace_root)
        except ValueError as exc:
            raise ContractValidationError(f"{label} escapes the ASEF workspace") from exc
        current = self.workspace_root
        for part in relative.parts:
            current = current / part
            if current.is_symlink() or self._is_junction(current):
                raise ContractValidationError(f"{label} contains a link or junction")
        candidate = absolute.resolve()
        if not candidate.is_relative_to(self.workspace_root):
            raise ContractValidationError(f"{label} escapes the ASEF workspace")
        return candidate

    @staticmethod
    def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContractValidationError(f"duplicate JSON field: {key}")
            result[key] = value
        return result

    @staticmethod
    def _is_junction(path: Path) -> bool:
        return bool(hasattr(path, "is_junction") and path.is_junction())
