from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable, Iterable
from uuid import uuid4

from ..security_contracts import (
    CleanupKind,
    CleanupMode,
    CleanupReport,
    CleanupRequest,
    CleanupTargetObservation,
    CleanupTargetStatus,
    FilesystemTargetStatus,
    characterize_filesystem_safety,
    cleanup_plan_fingerprint,
    inspect_filesystem_target,
)
from .docker import CommandExecutor


_SUITE_ID = re.compile(
    r"^(?P<kind>smoke|security)-(?P<stamp>[0-9]{8}T[0-9]{6}Z)-[0-9a-f]{8}$"
)
_DOCTOR_ID = re.compile(
    r"^doctor-(?P<stamp>[0-9]{8}T[0-9]{6}Z)-[0-9a-f]{8}$"
)
_RUN_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
_MAX_TREE_ENTRIES = 50_000


class CleanupExecutor:
    def __init__(
        self,
        workspace_root: Path | None = None,
        docker_executor: CommandExecutor = subprocess.run,
        *,
        now: Callable[[], datetime] | None = None,
        recursive_apply_supported: bool | None = None,
    ) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.root = (self.workspace_root / ".asef").absolute()
        self.docker_executor = docker_executor
        self.now = now or (lambda: datetime.now(UTC))
        profile = characterize_filesystem_safety()
        self.recursive_apply_supported = (
            profile.recursive_apply_supported
            if recursive_apply_supported is None
            else recursive_apply_supported
        )

    def execute(self, request: CleanupRequest) -> CleanupReport:
        request.validate()
        self._validate_root()
        cleanup_id = f"cleanup-{self.now():%Y%m%dT%H%M%SZ}-{uuid4().hex[:8]}"
        planned = tuple(self._plan(request))
        plan_sha256 = cleanup_plan_fingerprint(request, planned)
        targets = (
            tuple(self._apply(target) for target in planned)
            if request.mode is CleanupMode.APPLY
            else planned
        )
        report = CleanupReport(
            cleanup_id=cleanup_id,
            request=request,
            plan_sha256=plan_sha256,
            targets=targets,
            planned=sum(item.status is CleanupTargetStatus.PLANNED for item in targets),
            deleted=sum(item.status is CleanupTargetStatus.DELETED for item in targets),
            failed=sum(item.status is CleanupTargetStatus.FAILED for item in targets),
            skipped=sum(item.status is CleanupTargetStatus.SKIPPED for item in targets),
        )
        report.validate()
        return report

    def _validate_root(self) -> None:
        if not self.root.exists():
            self.root.mkdir(parents=True)
        if not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("cleanup root is not a safe directory")
        if hasattr(self.root, "is_junction") and self.root.is_junction():
            raise ValueError("cleanup root cannot be a junction")
        if self.root != (self.workspace_root / ".asef").absolute():
            raise ValueError("cleanup root identity changed")

    def _plan(self, request: CleanupRequest) -> Iterable[CleanupTargetObservation]:
        kinds = (
            (
                CleanupKind.RUNS,
                CleanupKind.SMOKE,
                CleanupKind.SECURITY,
                CleanupKind.QUALITY,
                CleanupKind.DOCTOR,
                CleanupKind.LOGS,
                CleanupKind.CONTAINERS,
            )
            if request.kind is CleanupKind.ALL
            else (request.kind,)
        )
        observations: list[CleanupTargetObservation] = []
        for kind in kinds:
            if kind is CleanupKind.RUNS:
                observations.extend(self._plan_runs(request))
            elif kind in {CleanupKind.SMOKE, CleanupKind.SECURITY}:
                observations.extend(self._plan_suites(request, kind))
            elif kind is CleanupKind.QUALITY:
                observations.extend(
                    self._plan_quality(
                        request,
                        include_run_quality=request.kind is not CleanupKind.ALL,
                    )
                )
            elif kind is CleanupKind.DOCTOR:
                observations.extend(self._plan_doctor(request))
            elif kind is CleanupKind.LOGS:
                observations.extend(self._plan_logs(request))
            elif kind is CleanupKind.CONTAINERS:
                observations.extend(self._plan_containers(request))
        return sorted(observations, key=lambda item: item.target_ref)

    def _plan_runs(self, request: CleanupRequest) -> list[CleanupTargetObservation]:
        root = self.root / "runs"
        if not root.is_dir():
            return []
        return [
            self._directory_candidate(
                child,
                self._run_created_at(child),
                request,
            )
            for child in sorted(root.iterdir())
        ]

    def _plan_suites(
        self, request: CleanupRequest, kind: CleanupKind
    ) -> list[CleanupTargetObservation]:
        root = self.root / kind.value
        if not root.is_dir():
            return []
        observations = []
        for child in sorted(root.iterdir()):
            created = None
            match = _SUITE_ID.fullmatch(child.name)
            manifest = child / "suite.json"
            if match is not None and match.group("kind") == kind.value:
                created = self._timestamp(match.group("stamp"))
                if not self._json_identity(manifest, "suite_id", child.name):
                    created = None
            observations.append(self._directory_candidate(child, created, request))
        return observations

    def _plan_quality(
        self, request: CleanupRequest, *, include_run_quality: bool
    ) -> list[CleanupTargetObservation]:
        observations: list[CleanupTargetObservation] = []
        runs = self.root / "runs"
        if include_run_quality and runs.is_dir():
            for run in sorted(runs.iterdir()):
                quality = run / "quality"
                if quality.exists():
                    observations.append(
                        self._directory_candidate(
                            quality, self._run_created_at(run), request
                        )
                    )
        for child in sorted(self.root.glob("quality-evaluation-*")):
            observations.append(self._directory_candidate(child, None, request))
        return observations

    def _plan_doctor(self, request: CleanupRequest) -> list[CleanupTargetObservation]:
        root = self.root / "doctor"
        if not root.is_dir():
            return []
        observations = []
        for child in sorted(root.iterdir()):
            created = None
            match = _DOCTOR_ID.fullmatch(child.name)
            if match is not None:
                created = self._timestamp(match.group("stamp"))
                if not self._json_identity(child / "report.json", "report_id", child.name):
                    created = None
            observations.append(self._directory_candidate(child, created, request))
        return observations

    def _plan_logs(self, request: CleanupRequest) -> list[CleanupTargetObservation]:
        root = self.root / "logs"
        if not root.is_dir():
            return []
        observations = []
        for child in sorted(root.glob("asef.jsonl*")):
            created = self._last_log_timestamp(child)
            observations.append(self._file_candidate(child, created, request))
        return observations

    def _plan_containers(
        self, request: CleanupRequest
    ) -> list[CleanupTargetObservation]:
        completed = self._docker(
            [
                "docker",
                "ps",
                "--no-trunc",
                "-aq",
                "--filter",
                "label=com.asef.managed=true",
            ]
        )
        if completed.returncode != 0:
            return [
                self._synthetic(
                    ".asef/containers/inspection",
                    CleanupTargetStatus.FAILED,
                    "CONTAINER_INSPECTION_FAILED",
                )
            ]
        observations = []
        for container_id in sorted(
            line.strip() for line in completed.stdout.splitlines() if line.strip()
        ):
            if not re.fullmatch(r"[0-9a-f]{12,64}", container_id):
                observations.append(
                    self._synthetic(
                        ".asef/containers/invalid-"
                        + hashlib.sha256(container_id.encode()).hexdigest()[:8],
                        CleanupTargetStatus.SKIPPED,
                        "CONTAINER_ID_INVALID",
                    )
                )
                continue
            inspected = self._docker(
                [
                    "docker",
                    "inspect",
                    "--format",
                    '{"id":{{json .Id}},"created":{{json .Created}},'
                    '"managed":{{json (index .Config.Labels "com.asef.managed")}}}',
                    container_id,
                ]
            )
            try:
                value = json.loads(inspected.stdout) if inspected.returncode == 0 else {}
                created = datetime.fromisoformat(str(value["created"]).replace("Z", "+00:00"))
                valid = (
                    value.get("id") == container_id
                    and value.get("managed") == "true"
                    and created.tzinfo is not None
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                valid = False
                created = None
            ref = f".asef/containers/{container_id}"
            if not valid:
                observations.append(
                    self._synthetic(
                        ref, CleanupTargetStatus.SKIPPED, "CONTAINER_MANIFEST_INVALID"
                    )
                )
                continue
            identity = hashlib.sha256(inspected.stdout.encode("utf-8")).hexdigest()
            eligible = self._old_enough(created, request)
            observations.append(
                CleanupTargetObservation(
                    ref,
                    identity,
                    CleanupTargetStatus.PLANNED
                    if eligible
                    else CleanupTargetStatus.SKIPPED,
                    "TARGET_ELIGIBLE" if eligible else "TARGET_TOO_NEW",
                )
            )
        return observations

    def _directory_candidate(
        self,
        path: Path,
        created: datetime | None,
        request: CleanupRequest,
    ) -> CleanupTargetObservation:
        ref = self._ref(path)
        safety = inspect_filesystem_target(self.root, path)
        if safety is not FilesystemTargetStatus.SAFE_DIRECTORY:
            return self._synthetic(ref, CleanupTargetStatus.SKIPPED, safety.value)
        if created is None:
            return self._synthetic(
                ref, CleanupTargetStatus.SKIPPED, "MANIFEST_INVALID"
            )
        try:
            identity, size = self._tree_identity(path)
        except (OSError, ValueError):
            return self._synthetic(
                ref, CleanupTargetStatus.SKIPPED, "TARGET_INSPECTION_FAILED"
            )
        eligible = self._old_enough(created, request)
        return CleanupTargetObservation(
            ref,
            identity,
            CleanupTargetStatus.PLANNED if eligible else CleanupTargetStatus.SKIPPED,
            "TARGET_ELIGIBLE" if eligible else "TARGET_TOO_NEW",
            size,
        )

    def _file_candidate(
        self,
        path: Path,
        created: datetime | None,
        request: CleanupRequest,
    ) -> CleanupTargetObservation:
        ref = self._ref(path)
        if (
            not path.is_file()
            or path.is_symlink()
            or (hasattr(path, "is_junction") and path.is_junction())
        ):
            return self._synthetic(
                ref, CleanupTargetStatus.SKIPPED, "FILESYSTEM_UNSAFE"
            )
        if created is None:
            return self._synthetic(
                ref, CleanupTargetStatus.SKIPPED, "MANIFEST_INVALID"
            )
        try:
            identity, size = self._file_identity(path)
        except OSError:
            return self._synthetic(
                ref, CleanupTargetStatus.SKIPPED, "TARGET_INSPECTION_FAILED"
            )
        eligible = self._old_enough(created, request)
        return CleanupTargetObservation(
            ref,
            identity,
            CleanupTargetStatus.PLANNED if eligible else CleanupTargetStatus.SKIPPED,
            "TARGET_ELIGIBLE" if eligible else "TARGET_TOO_NEW",
            size,
        )

    def _apply(self, target: CleanupTargetObservation) -> CleanupTargetObservation:
        if target.status is not CleanupTargetStatus.PLANNED:
            return target
        if target.target_ref.startswith(".asef/containers/"):
            return self._apply_container(target)
        path = self.workspace_root / Path(target.target_ref)
        if path.is_file() and not path.is_symlink():
            try:
                identity, _ = self._file_identity(path)
                if identity != target.identity_sha256:
                    raise ValueError("identity changed")
                path.unlink()
                deleted = not path.exists()
            except (OSError, ValueError):
                deleted = False
            return replace(
                target,
                status=(
                    CleanupTargetStatus.DELETED
                    if deleted
                    else CleanupTargetStatus.FAILED
                ),
                reason_code="TARGET_DELETED" if deleted else "TARGET_REVALIDATION_FAILED",
            )
        if not self.recursive_apply_supported:
            return replace(
                target,
                status=CleanupTargetStatus.FAILED,
                reason_code="RECURSIVE_APPLY_UNSUPPORTED",
            )
        try:
            if (
                inspect_filesystem_target(self.root, path)
                is not FilesystemTargetStatus.SAFE_DIRECTORY
            ):
                raise ValueError("unsafe target")
            identity, _ = self._tree_identity(path)
            if identity != target.identity_sha256:
                raise ValueError("identity changed")
            shutil.rmtree(path)
            deleted = not path.exists()
        except (OSError, ValueError):
            deleted = False
        return replace(
            target,
            status=(
                CleanupTargetStatus.DELETED
                if deleted
                else CleanupTargetStatus.FAILED
            ),
            reason_code="TARGET_DELETED" if deleted else "TARGET_REVALIDATION_FAILED",
        )

    def _apply_container(
        self, target: CleanupTargetObservation
    ) -> CleanupTargetObservation:
        container_id = target.target_ref.rsplit("/", 1)[-1]
        inspected = self._docker(
            [
                "docker",
                "inspect",
                "--format",
                '{"id":{{json .Id}},"created":{{json .Created}},'
                '"managed":{{json (index .Config.Labels "com.asef.managed")}}}',
                container_id,
            ]
        )
        if (
            inspected.returncode != 0
            or hashlib.sha256(inspected.stdout.encode("utf-8")).hexdigest()
            != target.identity_sha256
        ):
            return replace(
                target,
                status=CleanupTargetStatus.FAILED,
                reason_code="TARGET_REVALIDATION_FAILED",
            )
        removed = self._docker(["docker", "rm", "-f", container_id])
        absent = self._docker(["docker", "inspect", container_id]).returncode != 0
        deleted = removed.returncode == 0 and absent
        return replace(
            target,
            status=(
                CleanupTargetStatus.DELETED
                if deleted
                else CleanupTargetStatus.FAILED
            ),
            reason_code="TARGET_DELETED" if deleted else "CONTAINER_REMOVAL_FAILED",
        )

    def _run_created_at(self, run: Path) -> datetime | None:
        if _RUN_ID.fullmatch(run.name) is None:
            return None
        try:
            value = json.loads((run / "state.json").read_text(encoding="utf-8"))
            if value.get("run_id") != run.name:
                return None
            return datetime.fromisoformat(str(value["created_at"]).replace("Z", "+00:00"))
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def _json_identity(path: Path, field: str, expected: str) -> bool:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return isinstance(value, dict) and value.get(field) == expected
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return False

    def _last_log_timestamp(self, path: Path) -> datetime | None:
        try:
            latest = None
            for line in path.read_text(encoding="utf-8").splitlines():
                value = json.loads(line)
                timestamp = datetime.fromisoformat(
                    str(value["timestamp"]).replace("Z", "+00:00")
                )
                if timestamp.tzinfo is None:
                    return None
                latest = timestamp if latest is None or timestamp > latest else latest
            return latest
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def _old_enough(self, created: datetime, request: CleanupRequest) -> bool:
        if created.tzinfo is None:
            return False
        return created.astimezone(UTC) <= self.now() - timedelta(
            days=request.older_than_days
        )

    @staticmethod
    def _timestamp(value: str) -> datetime | None:
        try:
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        except ValueError:
            return None

    def _tree_identity(self, root: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        total = 0
        count = 0
        root_info = root.stat(follow_symlinks=False)
        for current, directories, files in os.walk(root, topdown=True, followlinks=False):
            base = Path(current)
            directories.sort()
            files.sort()
            for name in [*directories, *files]:
                count += 1
                if count > _MAX_TREE_ENTRIES:
                    raise ValueError("cleanup target exceeds entry budget")
                path = base / name
                if path.is_symlink() or (
                    hasattr(path, "is_junction") and path.is_junction()
                ):
                    raise ValueError("cleanup target contains a link")
                info = path.stat(follow_symlinks=False)
                if info.st_dev != root_info.st_dev:
                    raise ValueError("cleanup target crosses filesystem")
                relative = path.relative_to(root).as_posix()
                digest.update(
                    f"{relative}\0{info.st_mode}\0{info.st_size}\0"
                    f"{info.st_mtime_ns}\0{info.st_dev}\0{info.st_ino}\n".encode()
                )
                if stat.S_ISREG(info.st_mode):
                    total += info.st_size
                    with path.open("rb") as handle:
                        while chunk := handle.read(1024 * 1024):
                            digest.update(chunk)
        digest.update(
            f".\0{root_info.st_mode}\0{root_info.st_mtime_ns}\0"
            f"{root_info.st_dev}\0{root_info.st_ino}".encode()
        )
        return digest.hexdigest(), total

    @staticmethod
    def _file_identity(path: Path) -> tuple[str, int]:
        info = path.stat(follow_symlinks=False)
        digest = hashlib.sha256(
            f"{info.st_mode}\0{info.st_size}\0{info.st_mtime_ns}\0"
            f"{info.st_dev}\0{info.st_ino}\n".encode()
        )
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest(), info.st_size

    def _ref(self, path: Path) -> str:
        absolute = path.absolute()
        relative = absolute.relative_to(self.workspace_root.absolute()).as_posix()
        return relative

    @staticmethod
    def _synthetic(
        ref: str, status: CleanupTargetStatus, reason: str
    ) -> CleanupTargetObservation:
        identity = hashlib.sha256(f"{ref}\0{reason}".encode()).hexdigest()
        return CleanupTargetObservation(ref, identity, status, reason)

    def _docker(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            return self.docker_executor(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return subprocess.CompletedProcess(command, 125, "", "")
