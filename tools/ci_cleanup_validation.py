from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate installed asef cleanup in a controlled temporary root"
    )
    parser.add_argument(
        "--artifact-output",
        type=Path,
        default=Path(".asef/maintenance/cleanup"),
    )
    args = parser.parse_args(argv)
    output = args.artifact_output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    temporary_parent = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir()))
    with tempfile.TemporaryDirectory(
        prefix="asef-cleanup-ci-", dir=temporary_parent
    ) as directory:
        root = Path(directory)
        log = root / ".asef" / "logs" / "asef.jsonl.1"
        log.parent.mkdir(parents=True)
        log.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "timestamp": "2020-01-01T00:00:00+00:00",
                    "level": "INFO",
                    "logger": "asef",
                    "message": "controlled cleanup fixture",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        dry = _run(root, apply=False)
        if (dry["planned"], dry["deleted"], dry["failed"]) != (1, 0, 0):
            raise RuntimeError(f"unexpected cleanup dry-run result: {dry}")
        if not log.exists():
            raise RuntimeError("cleanup dry-run mutated the controlled log")
        applied = _run(root, apply=True)
        if (applied["planned"], applied["deleted"], applied["failed"]) != (0, 1, 0):
            raise RuntimeError(f"unexpected cleanup apply result: {applied}")
        if log.exists():
            raise RuntimeError("cleanup apply left the controlled log")
        for payload in (dry, applied):
            for key in ("report_json", "report_markdown"):
                source = (root / payload[key]).resolve(strict=True)
                if not source.is_relative_to((root / ".asef").resolve()):
                    raise RuntimeError("cleanup report escaped the controlled root")
                shutil.copy2(source, output / source.name)
    print(
        json.dumps(
            {
                "status": "SUCCEEDED",
                "dry_run_cleanup_id": dry["cleanup_id"],
                "apply_cleanup_id": applied["cleanup_id"],
            }
        )
    )
    return 0


def _run(root: Path, *, apply: bool) -> dict[str, object]:
    command = [
        "asef",
        "cleanup",
        "--kind",
        "logs",
        "--older-than-days",
        "7",
    ]
    if apply:
        command.append("--apply")
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("installed asef cleanup command failed")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("installed asef cleanup returned invalid JSON")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
