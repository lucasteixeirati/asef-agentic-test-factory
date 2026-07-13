from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CapabilityDeclaration:
    capability_id: str
    implementation_status: str
    adapter_id: str | None
    result_contract: str | None
    required_for_target: bool = False

    def validate(self) -> None:
        if not self.capability_id.strip():
            raise ValueError("capability_id is required")
        if self.implementation_status not in {"available", "partial", "planned", "unsupported"}:
            raise ValueError(f"invalid capability status: {self.implementation_status}")
        if self.implementation_status in {"available", "partial"} and not self.adapter_id:
            raise ValueError("available or partial capability requires adapter_id")


@dataclass(slots=True, frozen=True)
class LanguageProfile:
    id: str
    ecosystem: str
    image: str
    version_command: tuple[str, ...]
    current_support_level: str
    target_support_level: str
    project_markers: tuple[str, ...]
    capabilities: tuple[CapabilityDeclaration, ...]
    limitations: tuple[str, ...] = ()

    @property
    def test_capabilities(self) -> tuple[str, ...]:
        """Compatibility view used by the Stage 3 container conformance tests."""
        return tuple(item.capability_id for item in self.capabilities)

    def validate(self) -> None:
        if self.current_support_level not in {"reference", "supported", "experimental", "planned"}:
            raise ValueError(f"invalid current support level: {self.current_support_level}")
        if self.target_support_level not in {"reference", "supported", "experimental"}:
            raise ValueError(f"invalid target support level: {self.target_support_level}")
        if "@sha256:" not in self.image:
            raise ValueError("language profile image must be fixed by digest")
        if not self.version_command or not self.project_markers or not self.capabilities:
            raise ValueError("language profile command, markers and capabilities are required")
        ids = [item.capability_id for item in self.capabilities]
        if len(ids) != len(set(ids)):
            raise ValueError("language profile capability ids must be unique")
        for capability in self.capabilities:
            capability.validate()


LANGUAGE_PROFILES = {
    "python-pytest": LanguageProfile(
        id="python-pytest",
        ecosystem="python",
        image="python@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0",
        version_command=("python", "--version"),
        current_support_level="experimental",
        target_support_level="reference",
        project_markers=("pyproject.toml", "requirements.txt", "src/**/*.py"),
        capabilities=(
            CapabilityDeclaration("unit", "partial", "docker-unit-test", "NormalizedExecutionResult", True),
            CapabilityDeclaration("project-detection", "partial", "quality-context", None, True),
            CapabilityDeclaration("coverage", "planned", None, "CoverageResult", True),
            CapabilityDeclaration("mutation", "planned", None, "MutationResult", True),
            CapabilityDeclaration("backend-api", "planned", None, None),
            CapabilityDeclaration("performance", "planned", None, None),
        ),
        limitations=("pytest adapter pending Stage 5.2", "coverage and mutation adapters pending"),
    ),
    "node-typescript": LanguageProfile(
        id="node-typescript",
        ecosystem="node",
        image="node@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2",
        version_command=("node", "--version"),
        current_support_level="planned",
        target_support_level="supported",
        project_markers=("package.json", "package-lock.json", "tsconfig.json"),
        capabilities=tuple(
            CapabilityDeclaration(capability, "planned", None, None)
            for capability in ("unit", "web-ui", "backend-api", "coverage", "mutation", "performance")
        ),
        limitations=("container startup only; end-to-end profile pending Stage 6",),
    ),
    "java-junit": LanguageProfile(
        id="java-junit",
        ecosystem="java",
        image="eclipse-temurin@sha256:1ff763083f2993d57d0bf374ab10bb3e2cb873af6c13a04458ebbd3e0337dc76",
        version_command=("java", "-version"),
        current_support_level="planned",
        target_support_level="experimental",
        project_markers=("pom.xml", "build.gradle", "build.gradle.kts"),
        capabilities=tuple(
            CapabilityDeclaration(capability, "planned", None, None)
            for capability in ("unit", "backend-api", "coverage", "mutation", "performance", "mobile")
        ),
        limitations=("container startup only; tooling selection pending Stage 6",),
    ),
}


def get_language_profile(profile_id: str) -> LanguageProfile:
    try:
        profile = LANGUAGE_PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"unknown language profile: {profile_id}") from exc
    profile.validate()
    return profile
