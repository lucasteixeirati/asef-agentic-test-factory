from __future__ import annotations

import os
from pathlib import Path
import shutil
import unittest
from uuid import uuid4

from asef.adapters.java_unit_toolchain import DockerJavaUnitToolchainProbe


@unittest.skipUnless(os.environ.get("ASEF_RUN_JAVA_DOCKER_TESTS") == "1", "Java Docker tests disabled")
class JavaUnitToolchainDockerTests(unittest.TestCase):
    def test_maven_java_cache_and_isolation_probe_pass(self):
        Path(".asef").mkdir(exist_ok=True)
        root = Path(".asef") / f"java-toolchain-{uuid4().hex}"
        root.mkdir()
        try:
            workspace, output = DockerJavaUnitToolchainProbe.stage(root)
            os.chmod(output, 0o777)
            result = DockerJavaUnitToolchainProbe(root).execute(workspace, output)
        finally:
            shutil.rmtree(root)
        self.assertEqual("PASSED", result.status, result.diagnostic_code)
        self.assertNotEqual(0, result.uid)
        self.assertTrue(result.offline_cache_ready)
        self.assertTrue(result.egress_blocked)


if __name__ == "__main__": unittest.main()
