from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tarfile
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
    "sensitive assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|password|access[_-]?token|private[_-]?key|secret)"
        r"\b[\"']?\s*[:=]\s*[\"']?[^\s,;\"'}]{4,}"
    ),
}
MAX_TEXT_BYTES = 5 * 1024 * 1024
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10_000
ARCHIVE_SUFFIXES = (".whl", ".zip", ".tar", ".tar.gz", ".tgz")
TEXT_SUFFIXES = {
    ".cfg", ".csv", ".ini", ".json", ".jsonl", ".md", ".py", ".toml",
    ".txt", ".xml", ".yaml", ".yml",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan ASEF text artifacts for secret signatures")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args(argv)
    findings: list[str] = []
    errors: list[str] = []
    for label, content in _text_inputs(args.paths, errors):
        for pattern_name, pattern in PATTERNS.items():
            if pattern_name == "sensitive assignment" and not _assignment_scannable(label):
                continue
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                findings.append(f"{label}:{line}: {pattern_name}")
    if findings:
        print("Secret scan failed:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
    if errors:
        print("Secret scan incomplete:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    if findings:
        return 1
    if errors:
        return 2
    print("Secret scan passed: no known secret signatures found.")
    return 0


def _text_inputs(
    paths: list[Path], errors: list[str]
) -> Iterable[tuple[str, str]]:
    if not paths:
        for path in _tracked_files():
            yield from _path_inputs(path, errors)
        return
    for root in paths:
        if root.is_dir():
            candidates = _safe_directory_files(root, errors)
        else:
            candidates = (root,)
        for path in candidates:
            yield from _path_inputs(path, errors)


def _path_inputs(
    path: Path, errors: list[str]
) -> Iterable[tuple[str, str]]:
    label = path.as_posix()
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        errors.append(f"{label}: linked path rejected")
        return
    if not path.exists():
        errors.append(f"{label}: path is missing")
        return
    lowered = path.name.lower()
    if lowered.endswith((".whl", ".zip")):
        if zipfile.is_zipfile(path):
            yield from _zip_inputs(path, errors)
        else:
            errors.append(f"{label}: archive is invalid")
        return
    if lowered.endswith((".tar", ".tar.gz", ".tgz")):
        if tarfile.is_tarfile(path):
            yield from _tar_inputs(path, errors)
        else:
            errors.append(f"{label}: archive is invalid")
        return
    text = _read_text(path, errors)
    if text is not None:
        yield label, text


def _safe_directory_files(
    root: Path, errors: list[str]
) -> Iterable[Path]:
    if root.is_symlink() or (hasattr(root, "is_junction") and root.is_junction()):
        errors.append(f"{root.as_posix()}: linked directory rejected")
        return
    for current, directories, files in os.walk(root, followlinks=False):
        base = Path(current)
        retained: list[str] = []
        for name in sorted(directories):
            candidate = base / name
            if candidate.is_symlink() or (
                hasattr(candidate, "is_junction") and candidate.is_junction()
            ):
                errors.append(f"{candidate.as_posix()}: linked directory rejected")
            else:
                retained.append(name)
        directories[:] = retained
        for name in sorted(files):
            yield base / name


def _zip_inputs(
    path: Path, errors: list[str]
) -> Iterable[tuple[str, str]]:
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                errors.append(f"{path.as_posix()}: archive member limit exceeded")
                return
            total = 0
            for member in members:
                if member.is_dir():
                    continue
                if (member.external_attr >> 16) & 0o170000 == 0o120000:
                    errors.append(
                        f"{path.as_posix()}!{member.filename}: linked member rejected"
                    )
                    continue
                total += member.file_size
                if member.file_size > MAX_TEXT_BYTES or total > MAX_ARCHIVE_BYTES:
                    errors.append(
                        f"{path.as_posix()}!{member.filename}: archive size limit exceeded"
                    )
                    continue
                text = _decode(archive.read(member))
                if text is not None:
                    yield f"{path.as_posix()}!{member.filename}", text
    except (OSError, zipfile.BadZipFile):
        errors.append(f"{path.as_posix()}: archive cannot be read")


def _tar_inputs(
    path: Path, errors: list[str]
) -> Iterable[tuple[str, str]]:
    try:
        with tarfile.open(path, "r:*") as archive:
            members = archive.getmembers()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                errors.append(f"{path.as_posix()}: archive member limit exceeded")
                return
            total = 0
            for member in members:
                if member.issym() or member.islnk():
                    errors.append(
                        f"{path.as_posix()}!{member.name}: linked member rejected"
                    )
                    continue
                if not member.isfile():
                    continue
                total += member.size
                if member.size > MAX_TEXT_BYTES or total > MAX_ARCHIVE_BYTES:
                    errors.append(
                        f"{path.as_posix()}!{member.name}: archive size limit exceeded"
                    )
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    errors.append(
                        f"{path.as_posix()}!{member.name}: archive member unreadable"
                    )
                    continue
                text = _decode(extracted.read())
                if text is not None:
                    yield f"{path.as_posix()}!{member.name}", text
    except (OSError, tarfile.TarError):
        errors.append(f"{path.as_posix()}: archive cannot be read")


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    return [Path(item) for item in result.stdout.decode("utf-8").split("\0") if item]


def _read_text(path: Path, errors: list[str]) -> str | None:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            errors.append(f"{path.as_posix()}: file size limit exceeded")
            return None
        text = _decode(path.read_bytes())
        if text is None and path.suffix.lower() in TEXT_SUFFIXES:
            errors.append(f"{path.as_posix()}: text file is not valid UTF-8")
        return text
    except OSError:
        errors.append(f"{path.as_posix()}: file cannot be read")
        return None


def _decode(raw: bytes) -> str | None:
    if b"\0" in raw[:4096]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _assignment_scannable(label: str) -> bool:
    member = label.rsplit("!", 1)[-1].lower()
    return any(
        member.endswith(suffix)
        for suffix in (
            ".cfg", ".env", ".ini", ".json", ".jsonl", ".log",
            ".txt", ".xml", ".yaml", ".yml",
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
