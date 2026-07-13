from __future__ import annotations

import unittest

from asef.languages import LANGUAGE_PROFILES, get_language_profile


class LanguageProfileTests(unittest.TestCase):
    def test_reference_ecosystems_are_registered_by_digest(self) -> None:
        self.assertEqual(set(LANGUAGE_PROFILES), {"python-pytest", "node-typescript", "java-junit"})
        for profile in LANGUAGE_PROFILES.values():
            profile.validate()
            self.assertIn("@sha256:", profile.image)
            self.assertTrue(profile.version_command)
            self.assertIn("unit", profile.test_capabilities)

    def test_unknown_profile_is_explicit(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown language profile"):
            get_language_profile("unknown")
