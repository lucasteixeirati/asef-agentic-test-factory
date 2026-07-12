from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4


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


@dataclass(slots=True, frozen=True)
class ContainerResult:
    exit_code: int
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool
    timed_out: bool = False
    container_name: str = ""


class DockerRunner:
    def __init__(self, policy: DockerPolicy, executor: CommandExecutor = subprocess.run) -> None:
        self.policy = policy
        self.executor = executor

    def build_command(
        self,
        workspace: Path,
        command: list[str],
        *,
        container_name: str | None = None,
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

        mount = f"type=bind,src={resolved},dst=/workspace,readonly"
        return [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name or f"asef-{uuid4().hex}",
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
            "--mount",
            mount,
            "--workdir",
            "/workspace",
            self.policy.image,
            *command,
        ]

    def run(self, workspace: Path, command: list[str]) -> ContainerResult:
        container_name = f"asef-{uuid4().hex}"
        try:
            completed = self.executor(
                self.build_command(workspace, command, container_name=container_name),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.policy.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            self.executor(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                check=False,
            )
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
            )
        stdout, stdout_truncated = _truncate(completed.stdout, self.policy.stdout_limit_bytes)
        stderr, stderr_truncated = _truncate(completed.stderr, self.policy.stderr_limit_bytes)
        return ContainerResult(
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
            container_name=container_name,
        )


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
