from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "1.0.0"
WORKSPACE = Path("/workspace")
OUTPUT = Path("/asef-output")
MUTATION_WORKSPACE = Path("/tmp/asef-mutation")
DRIVER_RESULT = OUTPUT / "driver-result.json"
COVERAGE_NATIVE = OUTPUT / "native-coverage.json"
MUTATION_NATIVE = OUTPUT / "native-mutation.json"
MAX_CAPTURE_CHARS = 64 * 1024
MUTMUT_STATUS_BY_EXIT_CODE = {
    None: "not checked",
    0: "survived",
    1: "killed",
    2: "check was interrupted by user",
    3: "killed",
    5: "no tests",
    24: "timeout",
    33: "no tests",
    34: "skipped",
    35: "suspicious",
    36: "timeout",
    37: "caught by type check",
    152: "timeout",
    255: "timeout",
    -9: "segfault",
    -11: "segfault",
    -24: "timeout",
}


def _version(distribution: str) -> str:
    return importlib.metadata.version(distribution)


def _safe_paths(values: list[str]) -> tuple[str, ...]:
    if not values:
        raise ValueError("at least one relative path is required")
    result: list[str] = []
    for value in values:
        path = PurePosixPath(value)
        if (
            not value
            or "\\" in value
            or path.is_absolute()
            or ".." in path.parts
            or path == PurePosixPath(".")
            or path.as_posix() != value
        ):
            raise ValueError("quality paths must be canonical POSIX paths inside the workspace")
        candidate = (WORKSPACE / path).resolve(strict=True)
        if not candidate.is_relative_to(WORKSPACE.resolve(strict=True)):
            raise ValueError("quality path escapes the workspace")
        result.append(value)
    if len(result) != len(set(result)):
        raise ValueError("quality paths must be unique")
    return tuple(result)


def _configure_import_paths(paths: tuple[str, ...], *, root: Path = WORKSPACE) -> None:
    candidates = [root]
    for value in paths:
        first = PurePosixPath(value).parts[0]
        if first in {"src", "source"}:
            candidates.append(root / first)
    for candidate in reversed(candidates):
        resolved = str(candidate.resolve(strict=True))
        if resolved not in sys.path:
            sys.path.insert(0, resolved)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    content = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


def _driver_result(
    *,
    capability: str,
    tool_id: str,
    tool_version: str,
    status: str,
    diagnostic_code: str | None = None,
    diagnostic: str | None = None,
    **facts: Any,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "capability": capability,
        "tool_id": tool_id,
        "tool_version": tool_version,
        "status": status,
        "diagnostic_code": diagnostic_code,
        "diagnostic": diagnostic,
        **facts,
    }


def run_coverage(sources: list[str], tests: list[str]) -> int:
    source_paths = _safe_paths(sources)
    test_paths = _safe_paths(tests)
    _configure_import_paths(source_paths)
    import coverage
    import pytest

    collector = coverage.Coverage(
        branch=True,
        source=list(source_paths),
        data_file="/tmp/asef.coverage",
        config_file=False,
    )
    collector.start()
    try:
        pytest_exit = int(
            pytest.main(
                [
                    "-p",
                    "no:cacheprovider",
                    "--basetemp=/tmp/asef-pytest",
                    *test_paths,
                ]
            )
        )
    finally:
        collector.stop()
        collector.save()
    collector.json_report(outfile=str(COVERAGE_NATIVE), pretty_print=True)
    completed = pytest_exit == 0
    result = _driver_result(
        capability="coverage",
        tool_id="coverage.py",
        tool_version=_version("coverage"),
        status="COMPLETED" if completed else "FAILED",
        diagnostic_code=None if completed else "COVERAGE_TESTS_FAILED",
        diagnostic=None if completed else "The selected tests did not pass under coverage",
        scope=list(source_paths),
        test_paths=list(test_paths),
        pytest_exit_code=pytest_exit,
        native_result="native-coverage.json",
    )
    _write_json(DRIVER_RESULT, result)
    return 0 if completed else 4


def _run_mutmut(arguments: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("mutmut")
    if executable is None:
        raise RuntimeError("mutmut executable is unavailable")
    completed = subprocess.run(
        [executable, "run", "--max-children", "1", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    for value in (completed.stdout, completed.stderr):
        if value:
            print(value[:MAX_CAPTURE_CHARS], end="" if value.endswith("\n") else "\n")
    return completed


def _generate_mutmut_metadata(root: Path) -> None:
    previous = Path.cwd()
    try:
        os.chdir(root)
        os.environ["MUTANT_UNDER_TEST"] = "mutant_generation"
        from mutmut.__main__ import (
            copy_also_copy_files,
            copy_src_dir,
            create_mutants,
            setup_source_paths,
            store_lines_covered_by_tests,
        )
        from mutmut.configuration import Config

        Config.ensure_loaded()
        Path("mutants").mkdir(exist_ok=False)
        copy_src_dir()
        copy_also_copy_files()
        setup_source_paths()
        store_lines_covered_by_tests()
        create_mutants(max_children=1)
    finally:
        os.chdir(previous)


def _load_mutmut_metadata(root: Path) -> dict[str, int | None]:
    results: dict[str, int | None] = {}
    expected = {
        "exit_code_by_key",
        "type_check_error_by_key",
        "durations_by_key",
        "estimated_durations_by_key",
    }
    for path in sorted((root / "mutants").rglob("*.meta")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("mutmut metadata schema differs from the characterized 3.6.0 format")
        exit_codes = value["exit_code_by_key"]
        if not isinstance(exit_codes, dict):
            raise ValueError("mutmut exit_code_by_key must be an object")
        for name, exit_code in exit_codes.items():
            if (
                not isinstance(name, str)
                or not name.strip()
                or (exit_code is not None and not isinstance(exit_code, int))
                or name in results
            ):
                raise ValueError("mutmut metadata contains an invalid or duplicate mutant")
            results[name] = exit_code
    return results


def _mutation_native(
    exit_codes: dict[str, int | None], admitted: tuple[str, ...], max_mutants: int
) -> dict[str, Any]:
    admitted_set = set(admitted)
    mutants: list[dict[str, Any]] = []
    counts = {
        "killed": 0,
        "survived": 0,
        "invalid": 0,
        "timed_out": 0,
        "not_run": 0,
    }
    for name in sorted(exit_codes):
        native_status = MUTMUT_STATUS_BY_EXIT_CODE.get(exit_codes[name], "suspicious")
        reason = None
        if name not in admitted_set:
            normalized = "not_run"
            reason = "deferred_by_budget"
        elif native_status == "killed":
            normalized = "killed"
        elif native_status == "survived":
            normalized = "survived"
        elif native_status == "timeout":
            normalized = "timed_out"
        elif native_status in {"caught by type check", "suspicious", "segfault"}:
            normalized = "invalid"
        else:
            normalized = "not_run"
            reason = native_status
        counts[normalized] += 1
        mutants.append(
            {
                "name": name,
                "exit_code": exit_codes[name],
                "native_status": native_status,
                "normalized_status": normalized,
                "not_run_reason": reason,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_id": "mutmut",
        "tool_version": _version("mutmut"),
        "max_mutants": max_mutants,
        "mutants_total": len(exit_codes),
        "admitted": len(admitted),
        "deferred": len(exit_codes) - len(admitted),
        **counts,
        "mutants": mutants,
    }


def _write_mutmut_config(root: Path, sources: tuple[str, ...], tests: tuple[str, ...]) -> None:
    def array(values: tuple[str, ...]) -> str:
        return ", ".join(json.dumps(value) for value in values)

    content = (
        "[tool.mutmut]\n"
        f"source_paths = [{array(sources)}]\n"
        f"also_copy = [{array(tests)}]\n"
        f"pytest_add_cli_args_test_selection = [{array(tests)}]\n"
        "mutate_only_covered_lines = true\n"
        "use_git_change_detection = false\n"
    )
    (root / "pyproject.toml").write_text(content, encoding="utf-8", newline="\n")


def run_mutation(sources: list[str], tests: list[str], max_mutants: int) -> int:
    if max_mutants < 1:
        raise ValueError("max_mutants must be positive")
    source_paths = _safe_paths(sources)
    test_paths = _safe_paths(tests)
    if MUTATION_WORKSPACE.exists():
        raise FileExistsError("mutation workspace already exists")
    shutil.copytree(WORKSPACE, MUTATION_WORKSPACE, symlinks=False)
    _write_mutmut_config(MUTATION_WORKSPACE, source_paths, test_paths)

    try:
        _generate_mutmut_metadata(MUTATION_WORKSPACE)
    except Exception:
        _write_json(
            DRIVER_RESULT,
            _driver_result(
                capability="mutation",
                tool_id="mutmut",
                tool_version=_version("mutmut"),
                status="FAILED",
                diagnostic_code="MUTATION_DISCOVERY_FAILED",
                diagnostic="Mutmut could not generate the bounded discovery metadata",
                native_result=None,
            ),
        )
        return 7

    discovered = _load_mutmut_metadata(MUTATION_WORKSPACE)
    admitted = tuple(sorted(discovered)[:max_mutants])
    _write_json(MUTATION_NATIVE, _mutation_native(discovered, admitted, max_mutants))

    execution = _run_mutmut(list(admitted), MUTATION_WORKSPACE) if admitted else None
    observed = _load_mutmut_metadata(MUTATION_WORKSPACE)
    native = _mutation_native(observed, admitted, max_mutants)
    _write_json(MUTATION_NATIVE, native)
    failed = execution is not None and execution.returncode != 0
    inconclusive = any(
        item["native_status"] in {"suspicious", "segfault", "check was interrupted by user"}
        for item in native["mutants"]
        if item["name"] in set(admitted)
    )
    status = "FAILED" if failed else "PARTIAL" if inconclusive else "COMPLETED"
    _write_json(
        DRIVER_RESULT,
        _driver_result(
            capability="mutation",
            tool_id="mutmut",
            tool_version=_version("mutmut"),
            status=status,
            diagnostic_code=(
                "MUTATION_EXECUTION_FAILED"
                if failed
                else "MUTATION_INCONCLUSIVE_NATIVE_STATUS"
                if inconclusive
                else None
            ),
            diagnostic=(
                "Mutmut did not finish the admitted mutant execution"
                if failed
                else "One or more admitted mutants produced an inconclusive native status"
                if inconclusive
                else None
            ),
            scope=list(source_paths),
            test_paths=list(test_paths),
            native_result="native-mutation.json",
            discovered=native["mutants_total"],
            admitted=native["admitted"],
            deferred=native["deferred"],
        ),
    )
    return 7 if failed else 4 if inconclusive else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="asef-quality-driver")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("version")
    coverage_parser = subparsers.add_parser("coverage")
    coverage_parser.add_argument("--source", action="append", required=True)
    coverage_parser.add_argument("--tests", action="append", required=True)
    mutation_parser = subparsers.add_parser("mutation")
    mutation_parser.add_argument("--source", action="append", required=True)
    mutation_parser.add_argument("--tests", action="append", required=True)
    mutation_parser.add_argument("--max-mutants", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "version":
        versions = {
            "coverage": _version("coverage"),
            "mutmut": _version("mutmut"),
            "pytest": _version("pytest"),
        }
        print(json.dumps(versions, sort_keys=True))
        return 0
    try:
        if args.command == "coverage":
            return run_coverage(args.source, args.tests)
        return run_mutation(args.source, args.tests, args.max_mutants)
    except Exception as exc:
        diagnostic = f"Quality driver failed with {type(exc).__name__}"
        capability = args.command
        try:
            _write_json(
                DRIVER_RESULT,
                _driver_result(
                    capability=capability,
                    tool_id="coverage.py" if capability == "coverage" else "mutmut",
                    tool_version=_version("coverage" if capability == "coverage" else "mutmut"),
                    status="FAILED",
                    diagnostic_code="QUALITY_DRIVER_FAILED",
                    diagnostic=diagnostic or type(exc).__name__,
                    native_result=None,
                ),
            )
        except OSError:
            pass
        print(diagnostic, file=sys.stderr)
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
