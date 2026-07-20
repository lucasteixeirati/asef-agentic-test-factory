from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote


SCHEMA_VERSION = "1.0.0"
REQUIRED_PUBLIC_DOCS = (
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "docs/getting-started/quickstart.md",
    "docs/tutorials/wf-001-demo.md",
    "docs/tutorials/wf-001-live.md",
    "docs/guides/report-interpretation.md",
    "docs/guides/troubleshooting.md",
    "docs/architecture/alpha-python-architecture.md",
    "docs/project/support-and-limitations.md",
    "docs/contributing/adapter-guide.md",
)
USAGE_DOCS = (
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/getting-started/quickstart.md",
    "docs/tutorials/wf-001-demo.md",
    "docs/tutorials/wf-001-live.md",
    "docs/guides/report-interpretation.md",
    "docs/guides/troubleshooting.md",
    "docs/project/support-and-limitations.md",
)
REQUIRED_PATHS = (
    "src/asef/schemas/alpha-run-report.schema.json",
    "examples/context/python-alpha-smoke-context.json",
    "datasets/smoke",
    "datasets/security",
    "tooling/python-pytest",
    "tooling/python-quality",
)
REQUIRED_REPORT_HEADINGS = (
    "Executive summary",
    "Status and classification",
    "Requirement",
    "Analysis and traceability",
    "Attempts and functional result",
    "Oracle and human intervention",
    "Quality capabilities",
    "Budgets and usage",
    "Evidence",
    "Facts",
    "Inferences",
    "Recommendations",
    "Limitations",
    "How to interpret this result",
)
_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
_COMMAND = re.compile(
    r"(?m)^\s*(?:env\s+-u\s+[A-Z0-9_]+\s+)?(?:\S*[\\/])?asef(?:\.exe)?\s+([a-z][a-z0-9-]*)"
)
_PLACEHOLDER = re.compile(r"\b(?:TODO|FIXME|TBD|XXX)\b|\{\{[^}]+\}\}", re.IGNORECASE)
_ABSOLUTE_LOCAL = re.compile(r"^(?:[A-Za-z]:[\\/]|/|file:)", re.IGNORECASE)
_POSITIVE_FORBIDDEN = (
    re.compile(r"\bproduction[- ]ready\b", re.IGNORECASE),
    re.compile(r"\bsegur[oa]\s+para\s+produ[cç][aã]o\b", re.IGNORECASE),
    re.compile(r"\bcertificad[oa]\s+(?:para|por|como)\b", re.IGNORECASE),
    re.compile(r"\bsuporta(?:do|mos)?\s+(?:integralmente\s+)?(?:TypeScript|Java|macOS|Linux)\b", re.IGNORECASE),
)


@dataclass(slots=True, frozen=True)
class Finding:
    code: str
    path: str
    detail: str


@dataclass(slots=True, frozen=True)
class DocumentationAudit:
    root: str
    checked_files: int
    checked_links: int
    findings: tuple[Finding, ...]
    schema_version: str = SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "passed": self.passed,
            "checked_files": self.checked_files,
            "checked_links": self.checked_links,
            "findings": [asdict(item) for item in self.findings],
        }


class DocumentationChecker:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.findings: list[Finding] = []
        self.checked_links = 0
        self._texts: dict[Path, str] = {}
        self._anchors: dict[Path, set[str]] = {}

    def run(self) -> DocumentationAudit:
        files = self._discover_markdown()
        self._check_required_files()
        for path in files:
            text = self._read(path)
            self._check_links(path, text)
        self._check_version()
        self._check_public_commands()
        self._check_public_content()
        self._check_canonical_consistency()
        return DocumentationAudit(
            root=".",
            checked_files=len(files),
            checked_links=self.checked_links,
            findings=tuple(sorted(self.findings, key=lambda item: (item.path, item.code, item.detail))),
        )

    def _discover_markdown(self) -> tuple[Path, ...]:
        candidates = [
            self.root / "README.md",
            self.root / "CONTRIBUTING.md",
            self.root / "SECURITY.md",
            self.root / "CODE_OF_CONDUCT.md",
        ]
        docs = self.root / "docs"
        if docs.is_dir():
            candidates.extend(docs.rglob("*.md"))
        return tuple(sorted({path.resolve() for path in candidates if path.is_file()}))

    def _check_required_files(self) -> None:
        for relative in (*REQUIRED_PUBLIC_DOCS, *REQUIRED_PATHS):
            if not (self.root / relative).exists():
                self._add("REQUIRED_PATH_MISSING", relative, "required public path does not exist")

    def _read(self, path: Path) -> str:
        if path not in self._texts:
            try:
                self._texts[path] = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                self._add("MARKDOWN_UNREADABLE", self._relative(path), type(exc).__name__)
                self._texts[path] = ""
        return self._texts[path]

    def _check_links(self, source: Path, text: str) -> None:
        for match in _LINK.finditer(text):
            raw = match.group(1).strip()
            if not raw:
                self._add("LINK_EMPTY", self._relative(source), "empty markdown target")
                continue
            target = raw.split(maxsplit=1)[0].strip("<>")
            self.checked_links += 1
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if _ABSOLUTE_LOCAL.match(target):
                self._add("LOCAL_LINK_ABSOLUTE", self._relative(source), target)
                continue
            file_part, separator, anchor = target.partition("#")
            decoded_file = unquote(file_part)
            destination = source if not decoded_file else (source.parent / decoded_file).resolve()
            try:
                destination.relative_to(self.root)
            except ValueError:
                self._add("LINK_OUTSIDE_REPOSITORY", self._relative(source), target)
                continue
            if decoded_file and not destination.exists():
                self._add("LINK_TARGET_MISSING", self._relative(source), target)
                continue
            if separator and anchor:
                if not destination.is_file() or destination.suffix.lower() != ".md":
                    self._add("LINK_ANCHOR_NON_MARKDOWN", self._relative(source), target)
                    continue
                normalized = unquote(anchor).lower()
                if normalized not in self._anchors_for(destination):
                    self._add("LINK_ANCHOR_MISSING", self._relative(source), target)

    def _anchors_for(self, path: Path) -> set[str]:
        if path in self._anchors:
            return self._anchors[path]
        counts: dict[str, int] = {}
        anchors: set[str] = set()
        for match in _HEADING.finditer(self._read(path)):
            base = _slug(match.group(1))
            suffix = counts.get(base, 0)
            counts[base] = suffix + 1
            anchors.add(base if suffix == 0 else f"{base}-{suffix}")
        self._anchors[path] = anchors
        return anchors

    def _check_version(self) -> None:
        pyproject = self.root / "pyproject.toml"
        try:
            version = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
        except (OSError, UnicodeError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
            self._add("VERSION_UNREADABLE", "pyproject.toml", type(exc).__name__)
            return
        release_state_path = self.root / "docs/project/release-state.json"
        try:
            release_state = json.loads(release_state_path.read_text(encoding="utf-8"))
            published_version = release_state["latest_published_version"]
            published_tag = release_state["latest_published_tag"]
            development_version = release_state["development_version"]
            development_status = release_state["development_status"]
            if not all(
                isinstance(value, str) and value
                for value in (published_version, published_tag, development_version, development_status)
            ):
                raise TypeError("release state values must be non-empty strings")
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            self._add("RELEASE_STATE_UNREADABLE", "docs/project/release-state.json", type(exc).__name__)
            return
        if release_state.get("schema_version") != SCHEMA_VERSION:
            self._add(
                "RELEASE_STATE_SCHEMA",
                "docs/project/release-state.json",
                f"expected {SCHEMA_VERSION}",
            )
        if development_version != str(version):
            self._add(
                "DEVELOPMENT_VERSION_DIVERGENCE",
                "docs/project/release-state.json",
                f"state is {development_version}; package metadata is {version}",
            )
        if published_tag != f"v{published_version}":
            self._add(
                "PUBLISHED_TAG_DIVERGENCE",
                "docs/project/release-state.json",
                f"tag {published_tag}; expected v{published_version}",
            )
        canonical_release_docs = (
            "README.md",
            "docs/getting-started/quickstart.md",
            "docs/project/support-and-limitations.md",
        )
        for relative in canonical_release_docs:
            path = self.root / relative
            if not path.is_file():
                continue
            content = self._read(path)
            if development_version not in content:
                self._add(
                    "VERSION_DIVERGENCE",
                    relative,
                    f"missing development version {development_version}",
                )
            if published_version not in content:
                self._add(
                    "PUBLISHED_VERSION_MISSING",
                    relative,
                    f"missing latest published version {published_version}",
                )
        claim = re.compile(
            r"(?:A última (?:pré-)?release publicada|A última versão publicada)[^\n]*?`?v?"
            r"(?P<version>[0-9]+\.[0-9]+\.[0-9]+a[0-9]+)`?",
            re.IGNORECASE,
        )
        for relative in canonical_release_docs:
            path = self.root / relative
            if not path.is_file():
                continue
            for match in claim.finditer(self._read(path)):
                claimed = match.group("version")
                if claimed != published_version:
                    self._add(
                        "RELEASE_CLAIM_DIVERGENCE",
                        relative,
                        f"claims {claimed}; latest published version is {published_version}",
                    )

    def _check_public_commands(self) -> None:
        try:
            source = self.root / "src"
            sys.path.insert(0, str(source))
            from asef.cli import build_parser

            parser = build_parser()
            subparser_action = next(
                action for action in parser._actions if hasattr(action, "choices") and action.choices
            )
            known = set(subparser_action.choices)
        except Exception as exc:
            self._add("CLI_HELP_UNAVAILABLE", "src/asef/cli.py", type(exc).__name__)
            return
        finally:
            if sys.path and sys.path[0] == str(self.root / "src"):
                sys.path.pop(0)

        for relative in USAGE_DOCS:
            path = self.root / relative
            if not path.is_file():
                continue
            for command in _COMMAND.findall(self._read(path)):
                if command not in known:
                    self._add("PUBLIC_COMMAND_UNKNOWN", relative, command)

    def _check_public_content(self) -> None:
        for relative in USAGE_DOCS:
            path = self.root / relative
            if not path.is_file():
                continue
            text = self._read(path)
            placeholder = _PLACEHOLDER.search(text)
            if placeholder:
                self._add("PUBLIC_PLACEHOLDER", relative, placeholder.group(0))
            for pattern in _POSITIVE_FORBIDDEN:
                match = pattern.search(text)
                if match:
                    self._add("FORBIDDEN_CLAIM", relative, match.group(0))

    def _check_canonical_consistency(self) -> None:
        readme = self._read(self.root / "README.md") if (self.root / "README.md").is_file() else ""
        support_path = self.root / "docs/project/support-and-limitations.md"
        support = self._read(support_path) if support_path.is_file() else ""
        required_readme_links = (
            "docs/project/support-and-limitations.md",
            "docs/getting-started/quickstart.md",
            "docs/guides/troubleshooting.md",
        )
        for target in required_readme_links:
            if target not in readme:
                self._add("README_CANONICAL_LINK_MISSING", "README.md", target)
        for phrase in ("`python-pytest` | experimental", "`node-typescript` | experimental", "`java-junit` | experimental"):
            if phrase not in support:
                self._add("SUPPORT_MATRIX_DIVERGENCE", self._relative(support_path), phrase)

    def _relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def _add(self, code: str, path: str, detail: str) -> None:
        self.findings.append(Finding(code, path, detail[:300]))


def _slug(heading: str) -> str:
    value = re.sub(r"<[^>]+>", "", heading)
    value = re.sub(r"[`*_~\[\]()]", "", value)
    value = value.lower().strip()
    value = "".join(character for character in value if character.isalnum() or character in " _-")
    return re.sub(r"[ _]+", "-", value)


def _write_audit(output: Path, audit: DocumentationAudit) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = audit.to_dict()
    json_text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    digest = hashlib.sha256(json_text.encode("utf-8")).hexdigest()
    (output / "documentation-audit.json").write_text(json_text, encoding="utf-8", newline="\n")
    lines = [
        "# Documentation audit",
        "",
        f"- Result: `{'PASS' if audit.passed else 'FAIL'}`",
        f"- Files: `{audit.checked_files}`",
        f"- Links: `{audit.checked_links}`",
        f"- Findings: `{len(audit.findings)}`",
        f"- JSON SHA-256: `{digest}`",
        "",
    ]
    if audit.findings:
        lines.extend(("## Findings", ""))
        lines.extend(f"- `{item.code}` `{item.path}` — {item.detail}" for item in audit.findings)
        lines.append("")
    (output / "documentation-audit.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ASEF public documentation offline")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    audit = DocumentationChecker(args.root).run()
    if args.output is not None:
        _write_audit(args.output, audit)
    print(json.dumps(audit.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if audit.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
