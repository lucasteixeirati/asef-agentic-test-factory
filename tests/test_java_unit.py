from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import hashlib
import json

from asef.adapters.java_maven_project import JavaMavenProjectDetector, JavaMavenProjectError
from asef.java_unit_contracts import JavaUnitContractError, JavaUnitScenario, JavaUnitTestPlan, java_unit_plan_from_dict
from asef.skills.java_unit import JavaUnitPolicy, JavaUnitPolicyError, JavaUnitSkill


ROOT = Path(__file__).resolve().parents[1]


class JavaUnitContractTests(unittest.TestCase):
    def plan(self, **changes):
        values = {"scenario_id": "SCN-001", "description": "Add two values", "operation": "add", "left": 2, "right": 3, "expected": 5}
        values.update(changes)
        return JavaUnitTestPlan("JAV-PLAN-001", (JavaUnitScenario(**values),))

    def test_valid_plan_round_trips(self):
        plan = self.plan()
        self.assertEqual(plan, java_unit_plan_from_dict(plan.to_dict()))

    def test_contract_rejects_code_unknown_fields_boolean_and_unbounded_values(self):
        for changes in ({"operation": "exec"}, {"left": True}, {"expected": 2**40}, {"description": "password" + chr(10)}):
            with self.subTest(changes=changes), self.assertRaises(JavaUnitContractError):
                self.plan(**changes).validate()
        raw = self.plan().to_dict(); raw["script"] = "System.exit(0)"
        with self.assertRaises(JavaUnitContractError): java_unit_plan_from_dict(raw)

    def test_exception_oracle_is_only_division_by_zero(self):
        self.plan(operation="divide", right=0, expected="ArithmeticException").validate()
        with self.assertRaises(JavaUnitContractError): self.plan(expected="ArithmeticException").validate()
        with self.assertRaises(JavaUnitContractError): self.plan(operation="divide", right=0, expected=0).validate()

    def test_plan_bounds_and_identity_are_closed(self):
        with self.assertRaises(JavaUnitContractError): JavaUnitTestPlan("WEB-WRONG", self.plan().scenarios).validate()
        with self.assertRaises(JavaUnitContractError): JavaUnitTestPlan("JAV-EMPTY", ()).validate()
        duplicate = self.plan().scenarios * 2
        with self.assertRaises(JavaUnitContractError): JavaUnitTestPlan("JAV-DUP", duplicate).validate()

    def test_contract_rejects_integer_overflow(self):
        for changes in (
            {"left": 2**31 - 1, "right": 1},
            {"operation": "subtract", "left": -(2**31), "right": 1},
            {"operation": "multiply", "left": 2**30, "right": 2},
            {"operation": "divide", "left": -(2**31), "right": -1},
        ):
            with self.subTest(changes=changes), self.assertRaises(JavaUnitContractError):
                self.plan(**changes).validate()

    def test_skill_rejects_sensitive_descriptions_and_budget_overrides(self):
        evidence = JavaUnitSkill().validate(self.plan())
        self.assertEqual((evidence["status"], evidence["network_scope"]), ("PASSED", "none"))
        with self.assertRaises(JavaUnitPolicyError): JavaUnitSkill().validate(self.plan(description="password=secret"))
        with self.assertRaises(JavaUnitPolicyError): JavaUnitSkill(JavaUnitPolicy(max_scenarios=0))


class JavaMavenProjectDetectorTests(unittest.TestCase):
    def test_detects_the_closed_java_21_maven_fixture(self):
        project = JavaMavenProjectDetector().detect(ROOT / "examples/java-junit")
        self.assertEqual((project.java_release, project.junit_version, project.surefire_version), ("21", "5.13.4", "3.5.5"))

    def test_rejects_custom_repository_and_symlink_source(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "fixture"
            shutil.copytree(ROOT / "examples/java-junit", root)
            pom = root / "pom.xml"
            pom.write_text(pom.read_text(encoding="utf-8").replace("<build>", "<repositories/><build>"), encoding="utf-8")
            with self.assertRaises(JavaMavenProjectError): JavaMavenProjectDetector().detect(root)

    def test_rejects_xml_entities_and_unknown_versions(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "fixture"
            shutil.copytree(ROOT / "examples/java-junit", root)
            pom = root / "pom.xml"
            original = pom.read_text(encoding="utf-8")
            for replacement in (original.replace("?>", "?><!DOCTYPE project [<!ENTITY x 'x'>]>", 1), original.replace("5.13.4", "LATEST")):
                pom.write_text(replacement, encoding="utf-8")
                with self.assertRaises(JavaMavenProjectError): JavaMavenProjectDetector().detect(root)

    def test_fixture_manifest_reconciles_exact_public_files(self):
        root = ROOT / "examples/java-junit"
        manifest = json.loads((root / "fixture-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["fixture_id"], "JAVA-CALCULATOR-001")
        self.assertEqual(manifest["operational_network"], "none")
        for relative, expected in manifest["files"].items():
            actual = "sha256:" + hashlib.sha256((root / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected)

    def test_toolchain_bootstrap_matches_the_public_fixture(self):
        public = ROOT / "examples/java-junit"
        bootstrap = ROOT / "tooling/java-junit/bootstrap"
        for relative in ("pom.xml", "src/main/java/com/asef/fixture/Calculator.java"):
            self.assertEqual((public / relative).read_bytes(), (bootstrap / relative).read_bytes())


if __name__ == "__main__": unittest.main()
