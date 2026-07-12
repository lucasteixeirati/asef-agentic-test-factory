from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LanguageProfile:
    id: str
    ecosystem: str
    image: str
    version_command: tuple[str, ...]
    test_capabilities: tuple[str, ...]


LANGUAGE_PROFILES = {
    "python-pytest": LanguageProfile(
        id="python-pytest",
        ecosystem="python",
        image="python@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0",
        version_command=("python", "--version"),
        test_capabilities=("unit", "backend-api", "mutation", "performance"),
    ),
    "node-typescript": LanguageProfile(
        id="node-typescript",
        ecosystem="node",
        image="node@sha256:16e22a550f3863206a3f701448c45f7912c6896a62de43add43bb9c86130c3e2",
        version_command=("node", "--version"),
        test_capabilities=("unit", "web-ui", "backend-api", "mutation", "performance"),
    ),
    "java-junit": LanguageProfile(
        id="java-junit",
        ecosystem="java",
        image="eclipse-temurin@sha256:1ff763083f2993d57d0bf374ab10bb3e2cb873af6c13a04458ebbd3e0337dc76",
        version_command=("java", "-version"),
        test_capabilities=("unit", "backend-api", "mutation", "performance", "mobile"),
    ),
}


def get_language_profile(profile_id: str) -> LanguageProfile:
    try:
        return LANGUAGE_PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"unknown language profile: {profile_id}") from exc
