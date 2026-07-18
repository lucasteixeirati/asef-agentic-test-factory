from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .observability import sanitize_text


class OpenApiContractError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class OpenApiOperation:
    method: str
    path: str
    expected_status: int
    operation_id: str | None = None
    summary: str | None = None

    def validate(self) -> None:
        if self.method not in {"GET", "HEAD", "OPTIONS"}:
            raise OpenApiContractError("only read-only OpenAPI operations are supported")
        if not self.path.startswith("/") or self.path.startswith("//") or "{" in self.path:
            raise OpenApiContractError("OpenAPI path must be concrete and relative to the authorized origin")
        if not 200 <= self.expected_status <= 299:
            raise OpenApiContractError("OpenAPI operation requires an explicit 2xx response")
        for value in (self.operation_id, self.summary):
            if value is not None and (not value.strip() or sanitize_text(value) != value):
                raise OpenApiContractError("OpenAPI operation metadata is blank or sensitive")


@dataclass(slots=True, frozen=True)
class OpenApiSummary:
    source_sha256: str
    openapi_version: str
    title: str
    operations: tuple[OpenApiOperation, ...]
    schema_version: str = "1.0.0"

    def validate(self) -> None:
        if self.schema_version != "1.0.0" or not self.openapi_version.startswith(("3.0.", "3.1.")):
            raise OpenApiContractError("only OpenAPI 3.0/3.1 JSON is supported")
        if len(self.source_sha256) != 64 or not self.title.strip() or sanitize_text(self.title) != self.title:
            raise OpenApiContractError("OpenAPI source identity or title is invalid")
        if not self.operations or len(self.operations) > 100:
            raise OpenApiContractError("OpenAPI summary must contain between 1 and 100 operations")
        identities = [(item.method, item.path) for item in self.operations]
        if len(identities) != len(set(identities)):
            raise OpenApiContractError("OpenAPI operations must be unique")
        for operation in self.operations:
            operation.validate()

    def prompt_value(self) -> list[dict[str, object]]:
        self.validate()
        return [
            {
                "method": item.method,
                "path": item.path,
                "expected_status": item.expected_status,
                "operation_id": item.operation_id,
                "summary": item.summary,
            }
            for item in self.operations
        ]


class OpenApiJsonLoader:
    def load(self, path: Path) -> OpenApiSummary:
        if not path.is_file() or path.stat().st_size > 1_048_576:
            raise OpenApiContractError("OpenAPI source must be a regular JSON file up to 1 MiB")
        raw_bytes = path.read_bytes()
        try:
            raw = json.loads(raw_bytes.decode("utf-8"), object_pairs_hook=self._object)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OpenApiContractError("OpenAPI source must be valid UTF-8 JSON") from exc
        if not isinstance(raw, dict):
            raise OpenApiContractError("OpenAPI root must be an object")
        self._reject_external_refs(raw)
        version = raw.get("openapi")
        info = raw.get("info")
        paths = raw.get("paths")
        if not isinstance(version, str) or not isinstance(info, dict) or not isinstance(paths, dict):
            raise OpenApiContractError("OpenAPI version, info and paths are required")
        title = info.get("title")
        if not isinstance(title, str):
            raise OpenApiContractError("OpenAPI info.title must be a string")
        operations: list[OpenApiOperation] = []
        for route, path_item in paths.items():
            if not isinstance(route, str) or not isinstance(path_item, dict):
                raise OpenApiContractError("OpenAPI paths must map strings to objects")
            if "{" in route:
                continue
            for method in ("get", "head", "options"):
                operation = path_item.get(method)
                if operation is None:
                    continue
                if not isinstance(operation, dict):
                    raise OpenApiContractError("OpenAPI operation must be an object")
                responses = operation.get("responses")
                if not isinstance(responses, dict):
                    raise OpenApiContractError("OpenAPI operation responses are required")
                success = sorted(
                    int(code) for code in responses
                    if isinstance(code, str) and len(code) == 3 and code.isdigit() and code.startswith("2")
                )
                if not success:
                    continue
                operation_id = operation.get("operationId")
                summary = operation.get("summary")
                if operation_id is not None and not isinstance(operation_id, str):
                    raise OpenApiContractError("OpenAPI operationId must be a string")
                if summary is not None and not isinstance(summary, str):
                    raise OpenApiContractError("OpenAPI summary must be a string")
                operations.append(
                    OpenApiOperation(method.upper(), route, success[0], operation_id, summary)
                )
        result = OpenApiSummary(
            hashlib.sha256(raw_bytes).hexdigest(),
            version,
            title,
            tuple(operations),
        )
        result.validate()
        return result

    @classmethod
    def _reject_external_refs(cls, value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "$ref" and (not isinstance(item, str) or not item.startswith("#/")):
                    raise OpenApiContractError("external OpenAPI references are forbidden")
                cls._reject_external_refs(item)
        elif isinstance(value, list):
            for item in value:
                cls._reject_external_refs(item)

    @staticmethod
    def _object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise OpenApiContractError(f"duplicate JSON key in OpenAPI source: {key}")
            value[key] = item
        return value
