from __future__ import annotations

import json
import logging
import tempfile
import unittest
from pathlib import Path

from asef.observability import (
    close_operational_logging,
    configure_operational_logging,
    sanitize_text,
)


class OperationalLoggingTests(unittest.TestCase):
    def tearDown(self) -> None:
        logger = logging.getLogger("asef")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

    def test_jsonl_log_has_operational_context_and_no_stdout_handler(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            logger = configure_operational_logging(Path(directory), "INFO")
            logger.info(
                "command_completed",
                extra={
                    "run_id": "run-1",
                    "operation": "run",
                    "component": "cli",
                    "status": "SUCCEEDED",
                    "exit_code": 0,
                },
            )
            payload = json.loads((Path(directory) / "asef.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(payload["run_id"], "run-1")
            self.assertEqual(payload["status"], "SUCCEEDED")
            self.assertEqual(payload["level"], "INFO")
            self.assertEqual(len(logger.handlers), 1)
            self._close_logger()

    def test_sensitive_values_are_redacted(self) -> None:
        raw_key = "sk-" + "A" * 24
        sanitized = sanitize_text(
            f'provider failed api_key=value123 "password": "hidden456" token={raw_key}'
        )
        self.assertNotIn(raw_key, sanitized)
        self.assertNotIn("value123", sanitized)
        self.assertNotIn("hidden456", sanitized)
        self.assertIn("[REDACTED]", sanitized)

    def test_reconfiguration_replaces_handlers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = configure_operational_logging(Path(directory), "DEBUG")
            second = configure_operational_logging(Path(directory), "WARNING")
            self.assertIs(first, second)
            self.assertEqual(len(second.handlers), 1)
            self.assertEqual(second.level, logging.WARNING)
            self._close_logger()

    @staticmethod
    def _close_logger() -> None:
        close_operational_logging(logging.getLogger("asef"))


if __name__ == "__main__":
    unittest.main()
