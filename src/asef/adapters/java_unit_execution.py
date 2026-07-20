from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from time import perf_counter
from xml.etree import ElementTree

from ..application.ports import ExecutionOutput
from ..contracts import TestExecutionOutcome
from ..java_unit_contracts import JavaUnitTestPlan, java_unit_plan_from_dict
from ..skills.java_unit import JavaUnitSkill
from .docker import CommandExecutor, DockerPolicy, DockerRunner
from .java_maven_project import JavaMavenProjectDetector
from .java_unit_compiler import JavaUnitTestCompiler
from .java_unit_toolchain import JAVA_UNIT_IMAGE, SUREFIRE_VERSION


MAX_SUREFIRE_BYTES = 2 * 1024 * 1024
_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


class DockerJavaUnitExecutor:
    command = ("run",)

    def __init__(self, allowed_workspace_root: Path, executor: CommandExecutor = subprocess.run,
                 *, image: str = JAVA_UNIT_IMAGE, timeout_seconds: int = 90) -> None:
        self.allowed_workspace_root = allowed_workspace_root
        self.executor = executor
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.last_image_id: str | None = None

    @staticmethod
    def stage(plan: JavaUnitTestPlan, root: Path) -> tuple[Path, Path]:
        JavaUnitSkill().validate(plan)
        artifact = JavaUnitTestCompiler.compile(plan)
        public_fixture = Path(__file__).resolve().parents[3] / "examples" / "java-junit"
        JavaMavenProjectDetector().detect(public_fixture)
        workspace, output = root / "workspace", root / "output"
        reports = output / "surefire"
        workspace.mkdir(parents=True, exist_ok=False)
        reports.mkdir(parents=True, exist_ok=False)
        for relative in ("pom.xml", "src/main/java/com/asef/fixture/Calculator.java", "fixture-manifest.json"):
            destination = workspace / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(public_fixture / relative, destination)
        target = workspace / artifact.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(artifact.source, encoding="utf-8", newline="\n")
        (workspace / "plan.json").write_text(
            json.dumps(plan.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        reports.chmod(0o777)
        return workspace, output

    def execute(self, workspace: Path, output: Path) -> ExecutionOutput:
        _, artifact = self._validate_staged_inputs(workspace)
        report_dir = output / "surefire"
        for residual in report_dir.glob("*"):
            if residual.is_file(): residual.unlink()
            else: raise ValueError("Surefire output contains a non-file entry")
        image_id = self._resolve_image_id()
        self.last_image_id = image_id
        started = perf_counter()
        container = DockerRunner(DockerPolicy(
            image=image_id, capability_id="java-unit-execution",
            allowed_workspace_root=self.allowed_workspace_root, cpus=1, memory="512m",
            pids_limit=128, timeout_seconds=self.timeout_seconds,
            stdout_limit_bytes=128 * 1024, stderr_limit_bytes=128 * 1024,
        ), self.executor).run(workspace, list(self.command), output_dir=output)
        duration_ms = max(0, round((perf_counter() - started) * 1000))
        xml = self._read_single_report(report_dir)
        summary = normalize_surefire_result(xml, container.exit_code, artifact.test_names,
                                            container.timed_out or not container.cleanup_succeeded)
        return ExecutionOutput(
            image_id, self.command, container.exit_code, duration_ms, container.stdout, container.stderr,
            summary[0], summary[1], summary[2], summary[3], summary[4], "maven-surefire", SUREFIRE_VERSION,
            summary[5], xml, "surefire.xml" if xml is not None else None,
            "application/junit+xml" if xml is not None else None, container.timed_out,
            container.stdout_truncated, container.stderr_truncated,
        )

    @staticmethod
    def _validate_staged_inputs(workspace: Path):
        plan_path = workspace / "plan.json"
        if plan_path.is_symlink() or not 0 < plan_path.stat().st_size <= 256 * 1024:
            raise ValueError("staged Java plan is invalid")
        raw = json.loads(plan_path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
        plan = java_unit_plan_from_dict(raw)
        JavaUnitSkill().validate(plan)
        artifact = JavaUnitTestCompiler.compile(plan)
        artifact_path = workspace / artifact.path
        if artifact_path.is_symlink(): raise ValueError("compiled Java artifact cannot be a symlink")
        actual = artifact_path.read_bytes()
        if actual != artifact.source.encode("utf-8") or hashlib.sha256(actual).hexdigest() != artifact.sha256:
            raise ValueError("compiled Java artifact does not match the reviewed plan")
        JavaMavenProjectDetector().detect(workspace)
        manifest_path = workspace / "fixture-manifest.json"
        if manifest_path.is_symlink() or not 0 < manifest_path.stat().st_size <= 64 * 1024:
            raise ValueError("staged Java fixture manifest is invalid")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)
        if set(manifest) != {"schema_version", "fixture_id", "language", "java_release", "build_system", "test_framework", "files", "operational_network", "mutable_source"}:
            raise ValueError("staged Java fixture manifest fields differ")
        expected_files = {"pom.xml", "src/main/java/com/asef/fixture/Calculator.java"}
        if not isinstance(manifest["files"], dict) or set(manifest["files"]) != expected_files:
            raise ValueError("staged Java fixture manifest file allowlist differs")
        if (manifest["schema_version"], manifest["fixture_id"], manifest["operational_network"], manifest["mutable_source"]) != ("1.0.0", "JAVA-CALCULATOR-001", "none", False):
            raise ValueError("staged Java fixture manifest identity differs")
        for relative, expected in manifest["files"].items():
            actual_hash = "sha256:" + hashlib.sha256((workspace / relative).read_bytes()).hexdigest()
            if actual_hash != expected:
                raise ValueError("staged Java fixture differs from its manifest")
        return plan, artifact

    @staticmethod
    def _read_single_report(report_dir: Path) -> str | None:
        items = list(report_dir.iterdir())
        if not items:
            return None
        if len(items) != 1 or not items[0].is_file() or items[0].is_symlink() or not items[0].name.startswith("TEST-") or items[0].suffix != ".xml":
            raise ValueError("Surefire evidence allowlist violation")
        if not 0 < items[0].stat().st_size <= MAX_SUREFIRE_BYTES:
            raise ValueError("Surefire XML is empty or oversized")
        return items[0].read_text(encoding="utf-8", errors="strict")

    def _resolve_image_id(self) -> str:
        completed = self.executor(
            ["docker", "image", "inspect", self.image, "--format", "{{.Id}}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15, check=False,
        )
        image_id = completed.stdout.strip().lower()
        if completed.returncode != 0 or not _IMAGE_ID.fullmatch(image_id):
            raise OSError(f"Java unit image {self.image!r} is unavailable or invalid")
        return image_id


def normalize_surefire_result(xml: str | None, exit_code: int, expected_names: tuple[str, ...],
                              infrastructure_failed: bool = False):
    failure = (None, None, None, None, None)
    if infrastructure_failed or exit_code in {124, 125, 126, 127, 137}:
        return (*failure, TestExecutionOutcome.INFRASTRUCTURE_ERROR)
    if xml is None:
        return (*failure, TestExecutionOutcome.TOOL_ERROR)
    try:
        if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper(): raise ValueError("active XML")
        root = ElementTree.fromstring(xml)
        if root.tag != "testsuite": raise ValueError("unexpected Surefire root")
        counts = tuple(_count(root.get(name, "0")) for name in ("tests", "failures", "errors", "skipped"))
        tests, failed, errors, skipped = counts
        names = tuple(node.get("name", "") for node in root if node.tag == "testcase")
        if (len(names) != tests or tests != len(expected_names)
                or len(set(names)) != len(names) or set(names) != set(expected_names)):
            raise ValueError("test identity mismatch")
        passed = tests - failed - errors - skipped
        if passed < 0: raise ValueError("invalid counters")
    except (ElementTree.ParseError, ValueError):
        return (*failure, TestExecutionOutcome.TOOL_ERROR)
    if tests == 0: outcome = TestExecutionOutcome.NO_TESTS
    elif errors: outcome = TestExecutionOutcome.TEST_ERROR
    elif failed: outcome = TestExecutionOutcome.ASSERTION_FAILURE
    elif exit_code == 0: outcome = TestExecutionOutcome.PASSED
    else: outcome = TestExecutionOutcome.TOOL_ERROR
    if outcome is TestExecutionOutcome.PASSED and exit_code != 0: outcome = TestExecutionOutcome.TOOL_ERROR
    return tests, passed, failed, errors, skipped, outcome


def _count(value: str) -> int:
    parsed = int(value)
    if parsed < 0: raise ValueError("negative Surefire counter")
    return parsed


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value: raise ValueError(f"duplicate JSON key in Java unit input: {key}")
        value[key] = item
    return value


def java_unit_functional_fingerprint(result: ExecutionOutput) -> str:
    functional = {
        "schema_version": "1.0.0",
        "tool_id": result.tool_id,
        "tool_version": result.tool_version,
        "outcome": result.outcome.value,
        "counters": {
            "tests": result.tests, "passed": result.passed, "failed": result.failed,
            "errors": result.errors, "skipped": result.skipped,
        },
        "timed_out": result.timed_out,
    }
    encoded = json.dumps(functional, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
