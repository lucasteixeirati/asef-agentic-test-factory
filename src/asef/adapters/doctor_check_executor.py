from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from time import perf_counter
from typing import Callable

from ..application.doctor_runner import DoctorRequest
from ..context import ContextValidationError, QualityContext
from ..security_contracts import (
    DOCTOR_CHECK_IDS,
    DoctorCategory,
    DoctorCheck,
    DoctorCheckStatus,
    DoctorRecommendation,
)
from .docker import CommandExecutor
from .pytest_execution import PYTEST_IMAGE
from .quality_execution import QUALITY_IMAGE


_DOCKER_VERSION = re.compile(r"Docker version ([0-9][0-9A-Za-z.+-]*)")
_SAFE_VERSION = re.compile(r"^[0-9][0-9A-Za-z.+-]{0,63}$")
_SAFE_ARCHITECTURE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,31}$")
_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_WILDCARDS = ("*", "?", "[")
_MAX_CONTEXT_BYTES = 1024 * 1024


@dataclass(slots=True, frozen=True)
class _CheckDefinition:
    category: DoctorCategory
    recommendation: DoctorRecommendation | None


_DEFINITIONS = {
    "python-version": _CheckDefinition(
        DoctorCategory.RUNTIME, DoctorRecommendation.USE_PYTHON_313
    ),
    "asef-package": _CheckDefinition(
        DoctorCategory.PACKAGE, DoctorRecommendation.REINSTALL_ASEF_PACKAGE
    ),
    "host-profile": _CheckDefinition(
        DoctorCategory.HOST, DoctorRecommendation.USE_SUPPORTED_HOST
    ),
    "output-root": _CheckDefinition(
        DoctorCategory.FILESYSTEM, DoctorRecommendation.FIX_OUTPUT_ROOT
    ),
    "docker-cli": _CheckDefinition(
        DoctorCategory.DOCKER, DoctorRecommendation.INSTALL_DOCKER_CLI
    ),
    "docker-daemon": _CheckDefinition(
        DoctorCategory.DOCKER, DoctorRecommendation.START_DOCKER_DAEMON
    ),
    "docker-linux-engine": _CheckDefinition(
        DoctorCategory.DOCKER, DoctorRecommendation.USE_DOCKER_LINUX_ENGINE
    ),
    "pytest-image": _CheckDefinition(
        DoctorCategory.DOCKER, DoctorRecommendation.BUILD_PYTEST_IMAGE
    ),
    "quality-image": _CheckDefinition(
        DoctorCategory.DOCKER, DoctorRecommendation.BUILD_QUALITY_IMAGE
    ),
    "context": _CheckDefinition(
        DoctorCategory.CONTEXT, DoctorRecommendation.FIX_CONTEXT
    ),
    "live-key-presence": _CheckDefinition(
        DoctorCategory.LIVE, DoctorRecommendation.CONFIGURE_LIVE_KEY
    ),
    "managed-containers": _CheckDefinition(
        DoctorCategory.MAINTENANCE,
        DoctorRecommendation.REVIEW_MANAGED_CONTAINERS,
    ),
}


class DoctorCheckExecutor:
    def __init__(
        self,
        executor: CommandExecutor = subprocess.run,
        *,
        timeout_seconds: int = 5,
        distribution_version: Callable[[str], str] = metadata.version,
        environ: dict[str, str] | None = None,
        workspace_root: Path | None = None,
    ) -> None:
        if timeout_seconds < 1 or timeout_seconds > 30:
            raise ValueError("doctor timeout must be between 1 and 30 seconds")
        self.executor = executor
        self.timeout_seconds = timeout_seconds
        self.timeout_ms = timeout_seconds * 1000
        self.distribution_version = distribution_version
        self.environ = os.environ if environ is None else environ
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self._docker_info_cache: tuple[dict[str, str] | None, str] | None = None

    def execute(self, request: DoctorRequest) -> tuple[DoctorCheck, ...]:
        request.validate()
        self._docker_info_cache = None
        handlers = {
            "python-version": self._python_version,
            "asef-package": self._asef_package,
            "host-profile": self._host_profile,
            "output-root": lambda: self._output_root(request.output_root),
            "docker-cli": self._docker_cli,
            "docker-daemon": self._docker_daemon,
            "docker-linux-engine": self._docker_linux_engine,
            "pytest-image": lambda: self._image(
                "pytest-image", PYTEST_IMAGE, required=True
            ),
            "quality-image": lambda: self._image(
                "quality-image", QUALITY_IMAGE, required=False
            ),
            "context": lambda: self._context(request.context_ref),
            "live-key-presence": lambda: self._live_key(request.mode),
            "managed-containers": self._managed_containers,
        }
        checks: list[DoctorCheck] = []
        for check_id in DOCTOR_CHECK_IDS:
            started = perf_counter()
            try:
                status, code, summary, facts, required = handlers[check_id]()
            except Exception:
                required = self._required(check_id, request)
                status = DoctorCheckStatus.FAIL if required else DoctorCheckStatus.WARN
                code = "DOCTOR_CHECK_FAILED"
                summary = "The diagnostic check failed internally."
                facts = {}
            definition = _DEFINITIONS[check_id]
            check = DoctorCheck(
                check_id=check_id,
                category=definition.category,
                required=required,
                status=status,
                diagnostic_code=code,
                summary=summary,
                duration_ms=max(0, round((perf_counter() - started) * 1000)),
                timeout_ms=self.timeout_ms,
                recommendation=(
                    definition.recommendation
                    if status in {DoctorCheckStatus.FAIL, DoctorCheckStatus.WARN}
                    else None
                ),
                facts=facts,
            )
            check.validate()
            checks.append(check)
        return tuple(checks)

    @staticmethod
    def _required(check_id: str, request: DoctorRequest) -> bool:
        if check_id == "context":
            return request.context_ref is not None
        if check_id == "managed-containers":
            return False
        if check_id == "live-key-presence":
            return request.mode == "live"
        return True

    def _python_version(
        self,
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        facts = {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro,
            "implementation": platform.python_implementation(),
        }
        supported = sys.version_info >= (3, 13)
        return (
            DoctorCheckStatus.PASS if supported else DoctorCheckStatus.FAIL,
            "PYTHON_VERSION_SUPPORTED" if supported else "PYTHON_VERSION_UNSUPPORTED",
            "Python runtime is supported." if supported else "Python 3.13 or newer is required.",
            facts,
            True,
        )

    def _asef_package(
        self,
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        distribution = "asef-agentic-test-factory"
        try:
            version = self.distribution_version(distribution)
        except metadata.PackageNotFoundError:
            return (
                DoctorCheckStatus.FAIL,
                "ASEF_PACKAGE_MISSING",
                "The ASEF distribution is not installed.",
                {"distribution": distribution},
                True,
            )
        return (
            DoctorCheckStatus.PASS,
            "ASEF_PACKAGE_AVAILABLE",
            "The ASEF distribution is installed.",
            {"distribution": distribution, "version": version},
            True,
        )

    def _host_profile(
        self,
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        system = platform.system()
        architecture = platform.machine()
        supported = system in {"Windows", "Linux"} and bool(architecture)
        return (
            DoctorCheckStatus.PASS if supported else DoctorCheckStatus.FAIL,
            "HOST_PROFILE_SUPPORTED" if supported else "HOST_PROFILE_UNSUPPORTED",
            "The host profile is supported."
            if supported
            else "The host profile is not supported by the current Alpha.",
            {"os": system.lower(), "architecture": architecture.lower(), "supported": supported},
            True,
        )

    def _output_root(
        self, output_root: Path
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        allowed = (self.workspace_root / ".asef").resolve()
        candidate = (
            (self.workspace_root / output_root).resolve()
            if not output_root.is_absolute()
            else output_root.resolve()
        )
        contained = candidate.is_relative_to(allowed)
        writable = False
        probe_removed = False
        probe = candidate / f".doctor-probe-{os.getpid()}"
        if contained:
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                with probe.open("x", encoding="utf-8") as handle:
                    handle.write("asef-doctor")
                writable = True
            except OSError:
                writable = False
            finally:
                try:
                    probe.unlink(missing_ok=True)
                    probe_removed = not probe.exists()
                except OSError:
                    probe_removed = False
        passed = contained and writable and probe_removed
        return (
            DoctorCheckStatus.PASS if passed else DoctorCheckStatus.FAIL,
            "OUTPUT_ROOT_READY" if passed else "OUTPUT_ROOT_INVALID",
            "The output root is contained and writable."
            if passed
            else "The output root is not safely usable.",
            {
                "contained": contained,
                "writable": writable,
                "probe_removed": probe_removed,
            },
            True,
        )

    def _docker_cli(
        self,
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        try:
            completed = self._run(["docker", "--version"])
        except FileNotFoundError:
            return (
                DoctorCheckStatus.FAIL,
                "DOCKER_CLI_MISSING",
                "The Docker CLI is not available.",
                {"available": False},
                True,
            )
        match = _DOCKER_VERSION.search(completed.stdout)
        available = completed.returncode == 0 and match is not None
        facts: dict[str, object] = {"available": available}
        if match is not None:
            facts["version"] = match.group(1)
        return (
            DoctorCheckStatus.PASS if available else DoctorCheckStatus.FAIL,
            "DOCKER_CLI_AVAILABLE" if available else "DOCKER_CLI_INVALID",
            "The Docker CLI is available."
            if available
            else "The Docker CLI did not return a valid version.",
            facts,
            True,
        )

    def _docker_daemon(
        self,
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        info, reason = self._docker_info()
        available = info is not None
        facts: dict[str, object] = {"available": available}
        if info is not None:
            facts["server_version"] = info["server_version"]
        return (
            DoctorCheckStatus.PASS if available else DoctorCheckStatus.FAIL,
            "DOCKER_DAEMON_AVAILABLE" if available else reason,
            "The Docker daemon is available."
            if available
            else "The Docker daemon is unavailable.",
            facts,
            True,
        )

    def _docker_linux_engine(
        self,
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        info, reason = self._docker_info()
        if info is None:
            return (
                DoctorCheckStatus.FAIL,
                reason,
                "Docker engine details are unavailable.",
                {},
                True,
            )
        linux = info["os_type"] == "linux"
        return (
            DoctorCheckStatus.PASS if linux else DoctorCheckStatus.FAIL,
            "DOCKER_LINUX_ENGINE" if linux else "DOCKER_ENGINE_UNSUPPORTED",
            "Docker is using a Linux engine."
            if linux
            else "The current Docker engine is not Linux.",
            {"os_type": info["os_type"], "architecture": info["architecture"]},
            True,
        )

    def _image(
        self, check_id: str, image: str, *, required: bool
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        try:
            completed = self._run(
                ["docker", "image", "inspect", "--format", "{{.Id}}", image]
            )
        except FileNotFoundError:
            completed = subprocess.CompletedProcess([], 127, "", "")
        image_id = completed.stdout.strip()
        available = completed.returncode == 0 and _IMAGE_ID.fullmatch(image_id) is not None
        facts: dict[str, object] = {"available": available}
        if available:
            facts["image_id"] = image_id
        return (
            (
                DoctorCheckStatus.PASS
                if available
                else DoctorCheckStatus.FAIL
                if required
                else DoctorCheckStatus.WARN
            ),
            f"{check_id.upper().replace('-', '_')}_AVAILABLE"
            if available
            else f"{check_id.upper().replace('-', '_')}_MISSING",
            "The Docker image is available."
            if available
            else (
                "The required Docker image is not available locally."
                if required
                else "The optional Docker image is not available locally."
            ),
            facts,
            required,
        )

    def _context(
        self, context_ref: Path | None
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        if context_ref is None:
            return (
                DoctorCheckStatus.SKIP,
                "CONTEXT_NOT_REQUESTED",
                "No context was requested.",
                {},
                False,
            )
        path = (
            (self.workspace_root / context_ref)
            if not context_ref.is_absolute()
            else context_ref
        )
        if (
            not path.is_file()
            or path.is_symlink()
            or (hasattr(path, "is_junction") and path.is_junction())
            or path.stat().st_size > _MAX_CONTEXT_BYTES
        ):
            return self._invalid_context()
        try:
            context = QualityContext.load(path)
            system = context.data["systems"][0]
            repository_ids = system.get("repository_ids", [])
            if len(repository_ids) != 1:
                return self._invalid_context()
            repositories = {
                item["id"]: item for item in context.data["repositories"]
            }
            repository = repositories[repository_ids[0]]
            if repository.get("language_profile") != "python-pytest":
                return self._invalid_context()
            skills = context.skills_for(system["id"])
            skill = next(
                (item for item in skills if item.get("id") == "unit"),
                skills[0] if skills else None,
            )
            if skill is None:
                return self._invalid_context()
            repository_ref = str(repository.get("repository_ref", ""))
            if not repository_ref.startswith("workspace:"):
                return self._invalid_context()
            repository_root = (
                self.workspace_root / repository_ref.removeprefix("workspace:")
            ).resolve()
            if not repository_root.is_relative_to(self.workspace_root):
                return self._invalid_context()
            for relative in repository.get("read_scope", []):
                if not isinstance(relative, str) or any(item in relative for item in _WILDCARDS):
                    return self._invalid_context()
                candidate = (repository_root / relative).resolve()
                if not candidate.is_relative_to(repository_root) or not candidate.is_file():
                    return self._invalid_context()
        except (OSError, KeyError, IndexError, TypeError, ContextValidationError, json.JSONDecodeError):
            return self._invalid_context()
        return (
            DoctorCheckStatus.PASS,
            "CONTEXT_VALID",
            "The quality context is valid for the Python profile.",
            {"valid": True, "system_id": system["id"], "skill_id": skill["id"]},
            True,
        )

    @staticmethod
    def _invalid_context(
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        return (
            DoctorCheckStatus.FAIL,
            "CONTEXT_INVALID",
            "The quality context is invalid for the requested profile.",
            {"valid": False},
            True,
        )

    def _live_key(
        self, mode: str
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        if mode == "demo":
            return (
                DoctorCheckStatus.SKIP,
                "LIVE_KEY_NOT_REQUIRED",
                "Live provider credentials are not required in demo mode.",
                {},
                False,
            )
        present = bool(self.environ.get("OPENAI_API_KEY"))
        return (
            DoctorCheckStatus.PASS if present else DoctorCheckStatus.FAIL,
            "LIVE_KEY_PRESENT" if present else "LIVE_KEY_MISSING",
            "The live provider credential is present."
            if present
            else "The live provider credential is not configured.",
            {"present": present},
            True,
        )

    def _managed_containers(
        self,
    ) -> tuple[DoctorCheckStatus, str, str, dict[str, object], bool]:
        try:
            completed = self._run(
                [
                    "docker",
                    "ps",
                    "-aq",
                    "--filter",
                    "label=com.asef.managed=true",
                ]
            )
        except FileNotFoundError:
            return (
                DoctorCheckStatus.SKIP,
                "MANAGED_CONTAINER_CHECK_UNAVAILABLE",
                "Managed containers could not be inspected.",
                {},
                False,
            )
        if completed.returncode != 0:
            return (
                DoctorCheckStatus.WARN,
                "MANAGED_CONTAINER_CHECK_FAILED",
                "Managed containers could not be inspected.",
                {},
                False,
            )
        count = sum(bool(line.strip()) for line in completed.stdout.splitlines())
        return (
            DoctorCheckStatus.PASS if count == 0 else DoctorCheckStatus.WARN,
            "NO_MANAGED_CONTAINERS" if count == 0 else "MANAGED_CONTAINERS_PRESENT",
            "No managed ASEF containers remain."
            if count == 0
            else "Managed ASEF containers remain and require review.",
            {"count": count},
            False,
        )

    def _docker_info(self) -> tuple[dict[str, str] | None, str]:
        if self._docker_info_cache is not None:
            return self._docker_info_cache
        template = (
            '{"server_version":{{json .ServerVersion}},'
            '"os_type":{{json .OSType}},'
            '"architecture":{{json .Architecture}}}'
        )
        try:
            completed = self._run(["docker", "info", "--format", template])
        except FileNotFoundError:
            self._docker_info_cache = (None, "DOCKER_CLI_MISSING")
            return self._docker_info_cache
        if completed.returncode != 0:
            self._docker_info_cache = (None, "DOCKER_DAEMON_UNAVAILABLE")
            return self._docker_info_cache
        try:
            value = json.loads(completed.stdout)
            if (
                not isinstance(value, dict)
                or not all(
                    isinstance(value.get(key), str) and value[key]
                    for key in ("server_version", "os_type", "architecture")
                )
                or _SAFE_VERSION.fullmatch(value["server_version"]) is None
                or value["os_type"].lower() not in {"linux", "windows"}
                or _SAFE_ARCHITECTURE.fullmatch(value["architecture"].lower()) is None
            ):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            self._docker_info_cache = (None, "DOCKER_INFO_INVALID")
            return self._docker_info_cache
        self._docker_info_cache = (
            {
                "server_version": value["server_version"],
                "os_type": value["os_type"].lower(),
                "architecture": value["architecture"].lower(),
            },
            "DOCKER_DAEMON_AVAILABLE",
        )
        return self._docker_info_cache

    def _run(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        return self.executor(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout_seconds,
            check=False,
        )
