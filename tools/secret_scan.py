from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Iterable


PATTERNS = {
    "OpenAI API key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
}
MAX_TEXT_BYTES = 5 * 1024 * 1024


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan ASEF text artifacts for secret signatures")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args(argv)
    findings: list[str] = []
    for label, content in _text_inputs(args.paths):
        for pattern_name, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                findings.append(f"{label}:{line}: {pattern_name}")
    if findings:
        print("Secret scan failed:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print("Secret scan passed: no known secret signatures found.")
    return 0


def _text_inputs(paths: list[Path]) -> Iterable[tuple[str, str]]:
    if not paths:
        for path in _tracked_files():
            text = _read_text(path)
            if text is not None:
                yield path.as_posix(), text
        return
    for root in paths:
        if root.is_dir():
            candidates = (item for item in root.rglob("*") if item.is_file())
        else:
            candidates = (root,)
        for path in candidates:
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        if member.is_dir() or member.file_size > MAX_TEXT_BYTES:
                            continue
                        text = _decode(archive.read(member))
                        if text is not None:
                            yield f"{path.as_posix()}!{member.filename}", text
            else:
                text = _read_text(path)
                if text is not None:
                    yield path.as_posix(), text


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    return [Path(item) for item in result.stdout.decode("utf-8").split("\0") if item]


def _read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return None
        return _decode(path.read_bytes())
    except OSError:
        return None


def _decode(raw: bytes) -> str | None:
    if b"\0" in raw[:4096]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
