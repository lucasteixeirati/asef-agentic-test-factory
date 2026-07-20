from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from ..java_unit_contracts import JavaUnitTestPlan


@dataclass(slots=True, frozen=True)
class CompiledTypeScriptUnitArtifact:
    path: str
    source: str
    sha256: str
    test_names: tuple[str, ...]


class TypeScriptUnitTestCompiler:
    path = "generated/asef-generated.test.ts"

    @classmethod
    def compile(cls, plan: JavaUnitTestPlan) -> CompiledTypeScriptUnitArtifact:
        plan.validate()
        tests, names = [], []
        operations = {"add": "+", "subtract": "-", "multiply": "*"}
        for index, scenario in enumerate(plan.scenarios, 1):
            slug = re.sub(r"[^A-Za-z0-9]", "_", scenario.scenario_id).lower()
            name = f"case_{index:03d}_{slug}"; names.append(name)
            if scenario.operation == "divide":
                expression = f"divide({scenario.left}, {scenario.right})"
            else:
                expression = f"({scenario.left} {operations[scenario.operation]} {scenario.right})"
            if scenario.expected == "ArithmeticException":
                assertion = f"assert.throws(() => {expression}, RangeError);"
            else:
                assertion = f"assert.strictEqual(Math.trunc({expression}), {scenario.expected});"
            tests.append(f'test("{name}", () => {{ {assertion} }});')
        source = (
            'import test from "node:test";\nimport assert from "node:assert/strict";\n\n'
            'function divide(left, right) { if (right === 0) throw new RangeError("division by zero"); return left / right; }\n\n'
            + "\n".join(tests) + "\n"
        )
        return CompiledTypeScriptUnitArtifact(cls.path, source, hashlib.sha256(source.encode()).hexdigest(), tuple(names))
