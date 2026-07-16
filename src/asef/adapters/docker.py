from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4
import re


class CommandExecutor(Protocol):
    def __call__(self, command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]: ...


@dataclass(slots=True, frozen=True)
class DockerPolicy:
    image: str
    allowed_workspace_root: Path | None = None
    cpus: float = 2.0
    memory: str = "1g"
    pids_limit: int = 128
    timeout_seconds: int = 120
    stdout_limit_bytes: int = 1_048_576
    stderr_limit_bytes: int = 1_048_576
    capability_id: str = "generic"
    verify_cleanup: bool = True


@dataclass(slots=True, frozen=True)
class ContainerResult:
    exit_code: int
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool
    timed_out: bool = False
    container_name: str = ""
    cleanup_succeeded: bool = True
    cleanup_diagnostic: str | None = None


@dataclass(slots=True, frozen=True)
class ContainerCleanupObservation:
    container_name: str
    removal_requested: bool
    absent: bool
    diagnostic_code: str | None = None


class DockerRunner:
    def __init__(self, policy: DockerPolicy, executor: CommandExecutor = subprocess.run) -> None:
        self.policy = policy
        self.executor = executor
        self.last_cleanup: ContainerCleanupObservation | None = None

    def build_command(
        self,
        workspace: Path,
        command: list[str],
        *,
        container_name: str | None = None,
        output_dir: Path | None = None,
    ) -> list[str]:
        resolved = workspace.resolve(strict=True)
        if not resolved.is_dir():
            raise ValueError("workspace must be a directory")
        if self.policy.allowed_workspace_root is not None:
            allowed_root = self.policy.allowed_workspace_root.resolve(strict=True)
            if not allowed_root.is_dir():
                raise ValueError("allowed workspace root must be a directory")
            try:
                resolved.relative_to(allowed_root)
            except ValueError as exc:
                raise ValueError("workspace escapes allowed root") from exc
        if not command or any("\x00" in item for item in command):
            raise ValueError("command must contain safe argument values")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,63}", self.policy.capability_id):
            raise ValueError("Docker capability_id is invalid")
        identity = container_name or f"asef-{uuid4().hex}"

        mount = f"type=bind,src={resolved},dst=/workspace,readonly"
        mounts = ["--mount", mount]
        if output_dir is not None:
            resolved_output = output_dir.resolve(strict=True)
            if not resolved_output.is_dir():
                raise ValueError("output directory must be a directory")
            if self.policy.allowed_workspace_root is not None:
                try:
                    resolved_output.relative_to(allowed_root)
                except ValueError as exc:
                    raise ValueError("output directory escapes allowed root") from exc
            if _paths_overlap(resolved, resolved_output):
                raise ValueError("writable output directory cannot overlap the readonly workspace")
            mounts.extend([
                "--mount",
                f"type=bind,src={resolved_output},dst=/asef-output",
            ])
        return [
            "docker",
            "run",
            "--rm",
            "--name",
            identity,
            "--label",
            "com.asef.managed=true",
            "--label",
            f"com.asef.capability={self.policy.capability_id}",
            "--label",
            f"com.asef.execution={identity}",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            str(self.policy.pids_limit),
            "--memory",
            self.policy.memory,
            "--memory-swap",
            self.policy.memory,
            "--cpus",
            str(self.policy.cpus),
            "--user",
            "65534:65534",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            *mounts,
            "--workdir",
            "/workspace",
            self.policy.image,
            *command,
        ]

    def run(
        self,
        workspace: Path,
        command: list[str],
        *,
        output_dir: Path | None = None,
    ) -> ContainerResult:
        container_name = f"asef-{uuid4().hex}"
        try:
            completed = self.executor(
                self.build_command(
                    workspace,
                    command,
                    container_name=container_name,
                    output_dir=output_dir,
                ),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.policy.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            cleanup = self._cleanup(container_name, force=True)
            stdout, stdout_truncated = _truncate(
                _timeout_text(exc.stdout), self.policy.stdout_limit_bytes
            )
            stderr, stderr_truncated = _truncate(
                _timeout_text(exc.stderr), self.policy.stderr_limit_bytes
            )
            return ContainerResult(
                exit_code=124,
                stdout=stdout,
                stderr=stderr,
                stdout_truncated=stdout_truncated,
                stderr_truncated=stderr_truncated,
                timed_out=True,
                container_name=container_name,
                cleanup_succeeded=cleanup.absent,
                cleanup_diagnostic=cleanup.diagnostic_code,
            )
        except BaseException:
            self._cleanup(container_name, force=True)
            raise
        cleanup = self._cleanup(container_name, force=False)
        stdout, stdout_truncated = _truncate(completed.stdout, self.policy.stdout_limit_bytes)
        stderr, stderr_truncated = _truncate(completed.stderr, self.policy.stderr_limit_bytes)
        return ContainerResult(
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
            container_name=container_name,
            cleanup_succeeded=cleanup.absent,
            cleanup_diagnostic=cleanup.diagnostic_code,
        )

    def managed_container_ids(self, capability_id: str | None = None) -> tuple[str, ...]:
        capability = capability_id or self.policy.capability_id
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,63}", capability):
            raise ValueError("Docker capability_id is invalid")
        inspection = self._docker(
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                "label=com.asef.managed=true",
                "--filter",
                f"label=com.asef.capability={capability}",
            ],
            timeout=10,
        )
        if inspection.returncode != 0:
            raise OSError("managed container inspection failed")
        return tuple(
            container_id.strip()
            for container_id in inspection.stdout.splitlines()
            if container_id.strip()
        )

    def _cleanup(self, container_name: str, *, force: bool) -> ContainerCleanupObservation:
        if not self.policy.verify_cleanup:
            observation = ContainerCleanupObservation(container_name, force, True)
            self.last_cleanup = observation
            return observation
        removal_requested = force
        if force:
            self._docker(["docker", "rm", "-f", container_name], timeout=15)
        inspection = self._docker(
            ["docker", "ps", "-aq", "--filter", f"name=^{container_name}$"],
            timeout=10,
        )
        if inspection.returncode != 0:
            observation = ContainerCleanupObservation(
                container_name, removal_requested, False, "CONTAINER_INSPECTION_FAILED"
            )
        elif inspection.stdout.strip():
            if not force:
                removal_requested = True
                self._docker(["docker", "rm", "-f", container_name], timeout=15)
                second = self._docker(
                    ["docker", "ps", "-aq", "--filter", f"name=^{container_name}$"],
                    timeout=10,
                )
                absent = second.returncode == 0 and not second.stdout.strip()
            else:
                absent = False
            observation = ContainerCleanupObservation(
                container_name,
                removal_requested,
                absent,
                None if absent else "CONTAINER_RESIDUAL",
            )
        else:
            observation = ContainerCleanupObservation(
                container_name, removal_requested, True
            )
        self.last_cleanup = observation
        return observation

    def _docker(
        self, command: list[str], *, timeout: int
    ) -> subprocess.CompletedProcess[str]:
        try:
            return self.executor(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return subprocess.CompletedProcess(command, 125, "", "")


def _truncate(value: str, byte_limit: int) -> tuple[str, bool]:
    encoded = value.encode("utf-8")
    if len(encoded) <= byte_limit:
        return value, False
    suffix = "\n...[truncated by ASEF]"
    allowed = max(byte_limit - len(suffix.encode("utf-8")), 0)
    truncated = encoded[:allowed].decode("utf-8", errors="ignore") + suffix
    return truncated, True


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _paths_overlap(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False
