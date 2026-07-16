from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path
from time import perf_counter

from ..contracts import ContractValidationError, UnitTestArtifact
from ..languages import get_language_profile
from ..security_contracts import (
    LoadedSecurityCase,
    SecurityCaseStatus,
    SecurityClassification,
    SecurityExecutionObservation,
    SecurityExecutorKind,
    inspect_filesystem_target,
)
from ..skills.unit import UnitSkill, UnitSkillPolicyError
from .docker import DockerPolicy, DockerRunner


_DOCKER_EXECUTORS = frozenset({
    SecurityExecutorKind.HOST_ENVIRONMENT,
    SecurityExecutorKind.DOCKER_NETWORK,
    SecurityExecutorKind.DOCKER_PIDS,
    SecurityExecutorKind.DOCKER_MEMORY,
    SecurityExecutorKind.DOCKER_TIMEOUT,
    SecurityExecutorKind.DOCKER_OUTPUT,
    SecurityExecutorKind.DOCKER_SOCKET,
})


class SecurityCaseExecutor:
    def __init__(self, *, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds
        self.image = get_language_profile("python-pytest").image

    def execute(
        self,
        loaded: LoadedSecurityCase,
        suite_dir: Path,
        fixture_text: str,
    ) -> SecurityExecutionObservation:
        started = perf_counter()
        workspace = suite_dir / "workspaces" / loaded.spec.case_id
        workspace.mkdir(parents=True, exist_ok=False)
        try:
            facts = self._execute(loaded.spec.executor, workspace, fixture_text)
            if loaded.spec.executor in _DOCKER_EXECUTORS:
                residuals = self._runner(workspace).managed_container_ids()
                if residuals:
                    raise OSError("managed security containers remain after execution")
                facts = {**facts, "managed_residual_count": 0}
            status = SecurityCaseStatus.PASSED
            classification = SecurityClassification.CONTROL_ENFORCED
            code = message = None
        except _Unsupported as exc:
            facts = {}
            status = SecurityCaseStatus.UNSUPPORTED
            classification = SecurityClassification.UNSUPPORTED_PRIMITIVE
            code, message = exc.code, str(exc)
        except _ControlFailure as exc:
            facts = exc.facts
            status = SecurityCaseStatus.FAILED
            classification = SecurityClassification.CONTROL_FAILED
            code, message = exc.code, str(exc)
        except (OSError, ValueError, RuntimeError) as exc:
            facts = {}
            status = SecurityCaseStatus.ERROR
            classification = SecurityClassification.INFRASTRUCTURE_ERROR
            code, message = "SECURITY_EXECUTOR_ERROR", type(exc).__name__
        return SecurityExecutionObservation(
            status=status,
            classification=classification,
            duration_ms=max(0, round((perf_counter() - started) * 1000)),
            facts=facts,
            diagnostic_code=code,
            diagnostic=message,
        )

    def _execute(
        self,
        executor: SecurityExecutorKind,
        workspace: Path,
        fixture_text: str,
    ) -> dict[str, object]:
        handlers = {
            SecurityExecutorKind.HOST_ENVIRONMENT: self._secret_absent,
            SecurityExecutorKind.DOCKER_NETWORK: self._network_blocked,
            SecurityExecutorKind.PATH_CONTAINMENT: self._path_rejected,
            SecurityExecutorKind.FILESYSTEM_LINK: self._link_rejected,
            SecurityExecutorKind.DOCKER_PIDS: self._pids_limited,
            SecurityExecutorKind.DOCKER_MEMORY: self._memory_limited,
            SecurityExecutorKind.DOCKER_TIMEOUT: self._timeout_enforced,
            SecurityExecutorKind.DOCKER_OUTPUT: self._output_truncated,
            SecurityExecutorKind.STATIC_POLICY: self._policy_blocked,
            SecurityExecutorKind.AGENT_BOUNDARY: self._host_authority,
            SecurityExecutorKind.DOCKER_SOCKET: self._socket_absent,
            SecurityExecutorKind.ARTIFACT_CONTRACT: self._artifact_size_blocked,
        }
        return handlers[executor](workspace, fixture_text)

    def _runner(self, workspace: Path, **overrides: object) -> DockerRunner:
        values = {
            "image": self.image,
            "allowed_workspace_root": workspace.parent,
            "cpus": 1.0,
            "memory": "128m",
            "pids_limit": 32,
            "timeout_seconds": self.timeout_seconds,
            "stdout_limit_bytes": 4096,
            "stderr_limit_bytes": 4096,
            "capability_id": "security",
        }
        values.update(overrides)
        return DockerRunner(DockerPolicy(**values))

    def _json_docker(
        self, workspace: Path, script: str, **overrides: object
    ) -> tuple[dict[str, object], object]:
        result = self._runner(workspace, **overrides).run(
            workspace, ["python", "-c", script]
        )
        if result.exit_code != 0:
            raise OSError("security Docker probe failed")
        self._require_cleanup(result)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError("security Docker probe returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("security Docker probe must return an object")
        return payload, result

    def _secret_absent(self, workspace: Path, _: str) -> dict[str, object]:
        name = "ASEF_SECURITY_SENTINEL"
        previous = os.environ.get(name)
        os.environ[name] = "runtime-only-sentinel"
        try:
            payload, _result = self._json_docker(
                workspace,
                f"import json,os;print(json.dumps({{'sentinel_present':{name!r} in os.environ}}))",
            )
        finally:
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous
        if payload.get("sentinel_present") is not False:
            raise _ControlFailure("SECRET_VISIBLE", "Host sentinel reached the container", payload)
        return {"sentinel_present": False}

    def _network_blocked(self, workspace: Path, _: str) -> dict[str, object]:
        payload, _result = self._json_docker(
            workspace,
            "import json,socket\nblocked=False\n"
            "try: socket.create_connection(('1.1.1.1',53),timeout=1)\n"
            "except OSError: blocked=True\n"
            "print(json.dumps({'blocked':blocked}))",
        )
        if payload.get("blocked") is not True:
            raise _ControlFailure("NETWORK_AVAILABLE", "External connection was not blocked", payload)
        return {"network_blocked": True}

    def _path_rejected(self, workspace: Path, _: str) -> dict[str, object]:
        outside = workspace.parent.parent
        try:
            self._runner(workspace).build_command(outside, ["python", "-V"])
        except ValueError:
            return {"rejected_before_docker": True}
        raise _ControlFailure("PATH_ACCEPTED", "Outside path was accepted", {})

    def _link_rejected(self, workspace: Path, _: str) -> dict[str, object]:
        outside = workspace.parent / f"{workspace.name}-target"
        outside.mkdir()
        link = workspace / "escape-link"
        try:
            if platform.system() == "Windows":
                completed = subprocess.run(
                    [
                        "cmd.exe",
                        "/d",
                        "/c",
                        "mklink",
                        "/J",
                        str(link),
                        str(outside),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if completed.returncode != 0:
                    raise _Unsupported("LINK_PRIMITIVE_UNAVAILABLE", "Junction creation unavailable")
            else:
                os.symlink(outside, link, target_is_directory=True)
            observed = inspect_filesystem_target(workspace, link)
            if observed.value not in {"SYMBOLIC_LINK", "JUNCTION"}:
                raise _ControlFailure("LINK_NOT_REJECTED", "Link was not classified", {})
            if not outside.exists():
                raise _ControlFailure(
                    "LINK_TARGET_MODIFIED", "Link target was not preserved", {}
                )
            return {"link_status": observed.value, "target_preserved": True}
        finally:
            if link.exists() or link.is_symlink():
                if link.is_symlink():
                    link.unlink()
                else:
                    os.rmdir(link)
            if outside.exists():
                outside.rmdir()

    def _pids_limited(self, workspace: Path, _: str) -> dict[str, object]:
        script = (
            "import json,subprocess,sys\nchildren=[];blocked=False\n"
            "try:\n"
            "  for _ in range(64): children.append(subprocess.Popen([sys.executable,'-c','import time;time.sleep(5)']))\n"
            "except (OSError,BlockingIOError): blocked=True\n"
            "finally:\n"
            "  [p.terminate() for p in children]\n  [p.wait() for p in children]\n"
            "print(json.dumps({'blocked':blocked,'spawned':len(children)}))"
        )
        payload, _result = self._json_docker(workspace, script, pids_limit=16)
        if payload.get("blocked") is not True:
            raise _ControlFailure("PID_LIMIT_NOT_ENFORCED", "Process fanout was not blocked", payload)
        return {"blocked": True, "spawned": int(payload.get("spawned", 0))}

    def _memory_limited(self, workspace: Path, _: str) -> dict[str, object]:
        result = self._runner(workspace, memory="64m").run(
            workspace, ["python", "-c", "x=bytearray(256*1024*1024);print(len(x))"]
        )
        if result.exit_code != 137:
            raise _ControlFailure(
                "MEMORY_LIMIT_NOT_ENFORCED",
                "Memory probe did not terminate with the expected limit",
                {"exit_code": result.exit_code},
            )
        self._require_cleanup(result)
        return {"exit_code": 137}

    def _timeout_enforced(self, workspace: Path, _: str) -> dict[str, object]:
        result = self._runner(workspace, timeout_seconds=1).run(
            workspace, ["python", "-c", "import time;time.sleep(30)"]
        )
        if not result.timed_out or result.exit_code != 124:
            raise _ControlFailure("TIMEOUT_NOT_ENFORCED", "Timeout was not observed", {})
        self._require_cleanup(result)
        return {"timed_out": True, "exit_code": 124}

    def _output_truncated(self, workspace: Path, _: str) -> dict[str, object]:
        result = self._runner(
            workspace, stdout_limit_bytes=256, stderr_limit_bytes=256
        ).run(
            workspace,
            ["python", "-c", "import sys;print('o'*2048);print('e'*2048,file=sys.stderr)"],
        )
        if not result.stdout_truncated or not result.stderr_truncated:
            raise _ControlFailure("OUTPUT_NOT_TRUNCATED", "Output limits were not observed", {})
        self._require_cleanup(result)
        return {"stdout_truncated": True, "stderr_truncated": True}

    def _policy_blocked(self, workspace: Path, _: str) -> dict[str, object]:
        del workspace
        artifact = UnitTestArtifact(
            "tests_generated/test_policy.py",
            "import socket\n\ndef test_policy():\n    assert socket is not None\n",
            ("SEC-009",),
        )
        try:
            UnitSkill().validate(artifact)
        except UnitSkillPolicyError:
            return {"blocked_before_execution": True}
        raise _ControlFailure("IMPORT_ALLOWED", "Forbidden import passed policy", {})

    def _host_authority(self, workspace: Path, fixture_text: str) -> dict[str, object]:
        del workspace
        artifact = UnitTestArtifact(
            "tests_generated/test_injection.py",
            fixture_text + "\nimport os\n\ndef test_injection():\n    assert os.getcwd()\n",
            ("SEC-010",),
        )
        try:
            UnitSkill().validate(artifact)
        except UnitSkillPolicyError:
            return {"host_policy_preserved": True, "artifact_rejected": True}
        raise _ControlFailure("HOST_AUTHORITY_CHANGED", "Injected instruction changed policy", {})

    def _socket_absent(self, workspace: Path, _: str) -> dict[str, object]:
        runner = self._runner(workspace)
        argv = runner.build_command(workspace, ["python", "-V"], container_name="asef-security-probe")
        labels = {
            item for item in argv if item.startswith("com.asef.")
        }
        if (
            "com.asef.managed=true" not in labels
            or "com.asef.capability=security" not in labels
            or any("docker.sock" in item for item in argv)
        ):
            raise _ControlFailure(
                "DOCKER_OWNERSHIP_POLICY_INVALID",
                "Docker ownership labels or mounts are invalid",
                {},
            )
        payload, _result = self._json_docker(
            workspace,
            "import json,os;print(json.dumps({'socket_present':os.path.exists('/var/run/docker.sock')}))",
        )
        if payload.get("socket_present") is not False:
            raise _ControlFailure("DOCKER_SOCKET_VISIBLE", "Docker socket is visible", payload)
        return {
            "socket_present": False,
            "ownership_labels_present": True,
            "socket_mount_absent": True,
        }

    def _artifact_size_blocked(self, workspace: Path, _: str) -> dict[str, object]:
        del workspace
        artifact = UnitTestArtifact(
            "tests_generated/test_large.py",
            "def test_large():\n    assert True\n#" + ("x" * (21 * 1024)),
            ("SEC-012",),
        )
        try:
            artifact.validate()
        except ContractValidationError:
            return {"blocked_before_persistence": True}
        raise _ControlFailure("OVERSIZED_ARTIFACT_ACCEPTED", "Oversized artifact was accepted", {})

    @staticmethod
    def _require_cleanup(result: object) -> None:
        if getattr(result, "cleanup_succeeded", True) is not True:
            raise OSError("managed container cleanup could not be verified")


class _Unsupported(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _ControlFailure(RuntimeError):
    def __init__(self, code: str, message: str, facts: dict[str, object]) -> None:
        super().__init__(message)
        self.code = code
        self.facts = facts
