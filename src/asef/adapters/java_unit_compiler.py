from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from ..java_unit_contracts import JavaUnitTestPlan


@dataclass(slots=True, frozen=True)
class CompiledJavaUnitArtifact:
    path: str
    source: str
    sha256: str
    test_names: tuple[str, ...]


class JavaUnitTestCompiler:
    path = "src/test/java/com/asef/generated/AsefGeneratedTest.java"

    @classmethod
    def compile(cls, plan: JavaUnitTestPlan) -> CompiledJavaUnitArtifact:
        plan.validate()
        methods: list[str] = []
        names: list[str] = []
        for index, scenario in enumerate(plan.scenarios, 1):
            slug = re.sub(r"[^A-Za-z0-9]", "_", scenario.scenario_id).lower()
            name = f"case_{index:03d}_{slug}"
            names.append(name)
            call = f"calculator.{scenario.operation}({scenario.left}, {scenario.right})"
            if scenario.expected == "ArithmeticException":
                body = f"assertThrows(ArithmeticException.class, () -> {call});"
            else:
                body = f"assertEquals({scenario.expected}, {call});"
            methods.append(f"    @Test void {name}() {{ {body} }}")
        source = (
            "package com.asef.generated;\n\n"
            "import com.asef.fixture.Calculator;\n"
            "import org.junit.jupiter.api.Test;\n"
            "import static org.junit.jupiter.api.Assertions.assertEquals;\n"
            "import static org.junit.jupiter.api.Assertions.assertThrows;\n\n"
            "final class AsefGeneratedTest {\n"
            "    private final Calculator calculator = new Calculator();\n\n"
            + "\n".join(methods)
            + "\n}\n"
        )
        return CompiledJavaUnitArtifact(
            cls.path, source, hashlib.sha256(source.encode("utf-8")).hexdigest(), tuple(names)
        )
