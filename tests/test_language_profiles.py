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

    def test_gate_6_promotes_only_observed_node_and_java_capabilities(self) -> None:
        node = get_language_profile("node-typescript")
        java = get_language_profile("java-junit")
        self.assertEqual((node.current_support_level, java.current_support_level), ("experimental", "experimental"))
        node_status = {item.capability_id: item.implementation_status for item in node.capabilities}
        java_status = {item.capability_id: item.implementation_status for item in java.capabilities}
        self.assertEqual((node_status["unit"], node_status["web-ui"], java_status["unit"]), ("partial", "partial", "partial"))
        self.assertEqual((node_status["coverage"], java_status["mutation"]), ("planned", "planned"))
