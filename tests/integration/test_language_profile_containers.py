from __future__ import annotations

import os
import unittest
from pathlib import Path

from asef_spike.docker_runner import DockerPolicy, DockerRunner
from asef_spike.language_profiles import LANGUAGE_PROFILES


@unittest.skipUnless(os.environ.get("ASEF_RUN_DOCKER_TESTS") == "1", "Docker tests disabled")
class LanguageProfileContainerTests(unittest.TestCase):
    workspace = Path(".asef/language-profile-workspace")

    @classmethod
    def setUpClass(cls) -> None:
        cls.workspace.mkdir(parents=True, exist_ok=True)

    def test_python_node_and_java_start_under_common_policy(self) -> None:
        for profile in LANGUAGE_PROFILES.values():
            with self.subTest(profile=profile.id):
                runner = DockerRunner(
                    DockerPolicy(
                        image=profile.image,
                        allowed_workspace_root=Path(".asef"),
                        cpus=1,
                        memory="256m",
                        pids_limit=64,
                        timeout_seconds=20,
                    )
                )
                result = runner.run(self.workspace, list(profile.version_command))
                self.assertEqual(result.exit_code, 0, result.stderr)
                self.assertFalse(result.timed_out)
                self.assertTrue((result.stdout + result.stderr).strip())
