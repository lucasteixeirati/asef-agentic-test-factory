from __future__ import annotations

import tempfile
import tomllib
import unittest
from pathlib import Path

from tools.docs_check import DocumentationChecker, _slug


ROOT = Path(__file__).resolve().parents[1]


class DocumentationCheckerTests(unittest.TestCase):
    def test_repository_public_documentation_passes_offline(self) -> None:
        audit = DocumentationChecker(ROOT).run()
        self.assertTrue(audit.passed, list(audit.findings))
        self.assertGreaterEqual(audit.checked_files, 100)
        self.assertGreater(audit.checked_links, 0)

    def test_missing_target_anchor_absolute_link_and_placeholder_are_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "# Home\n\n[missing](missing.md) [anchor](#absent) "
                "[absolute](C:/private/file.md) TODO\n",
                encoding="utf-8",
            )
            audit = DocumentationChecker(root).run()
        codes = {item.code for item in audit.findings}
        self.assertIn("LINK_TARGET_MISSING", codes)
        self.assertIn("LINK_ANCHOR_MISSING", codes)
        self.assertIn("LOCAL_LINK_ABSOLUTE", codes)
        self.assertIn("PUBLIC_PLACEHOLDER", codes)

    def test_github_style_slug_is_deterministic_for_accents_and_duplicates(self) -> None:
        self.assertEqual(_slug("Segurança e limitações"), "segurança-e-limitações")
        self.assertEqual(_slug("`AlphaRunReport` 1.0.0"), "alpharunreport-100")

    def test_source_fallback_versions_match_package_metadata(self) -> None:
        version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        for relative in ("src/asef/cli.py", "src/asef/application/build_alpha_report.py"):
            self.assertIn(f'return "{version}"', (ROOT / relative).read_text(encoding="utf-8"))

    def test_stale_canonical_release_claim_is_a_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs/getting-started").mkdir(parents=True)
            (root / "docs/project").mkdir(parents=True)
            (root / "pyproject.toml").write_text(
                '[project]\nname = "fixture"\nversion = "0.1.0a7"\n',
                encoding="utf-8",
            )
            (root / "docs/project/release-state.json").write_text(
                '{"schema_version":"1.0.0","latest_published_version":"0.1.0a6",'
                '"latest_published_tag":"v0.1.0a6","development_version":"0.1.0a7",'
                '"development_status":"CANDIDATE"}',
                encoding="utf-8",
            )
            (root / "README.md").write_text(
                "# Fixture\n\nA última pré-release publicada é `v0.1.0a5`. Candidata `0.1.0a7`.\n",
                encoding="utf-8",
            )
            (root / "docs/getting-started/quickstart.md").write_text(
                "# Quickstart\n\nA última pré-release publicada é `v0.1.0a6`. Candidata `0.1.0a7`.\n",
                encoding="utf-8",
            )
            (root / "docs/project/support-and-limitations.md").write_text(
                "# Support\n\nA última versão publicada é `0.1.0a6`. Candidata `0.1.0a7`.\n",
                encoding="utf-8",
            )
            audit = DocumentationChecker(root).run()
        divergences = [item for item in audit.findings if item.code == "RELEASE_CLAIM_DIVERGENCE"]
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].path, "README.md")

    def test_release_state_must_match_package_metadata_and_published_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs/project").mkdir(parents=True)
            (root / "pyproject.toml").write_text(
                '[project]\nname = "fixture"\nversion = "0.1.0a7"\n',
                encoding="utf-8",
            )
            (root / "docs/project/release-state.json").write_text(
                '{"schema_version":"1.0.0","latest_published_version":"0.1.0a6",'
                '"latest_published_tag":"v0.1.0a5","development_version":"0.1.0a8",'
                '"development_status":"CANDIDATE"}',
                encoding="utf-8",
            )
            audit = DocumentationChecker(root).run()
        codes = {item.code for item in audit.findings}
        self.assertIn("DEVELOPMENT_VERSION_DIVERGENCE", codes)
        self.assertIn("PUBLISHED_TAG_DIVERGENCE", codes)


if __name__ == "__main__":
    unittest.main()
