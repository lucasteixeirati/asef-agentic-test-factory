from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


class JavaMavenProjectError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class JavaMavenProject:
    root: Path
    pom: Path
    source_root: Path
    java_release: str
    junit_version: str
    surefire_version: str
    schema_version: str = "1.0.0"


class JavaMavenProjectDetector:
    _NS = {"m": "http://maven.apache.org/POM/4.0.0"}
    _REQUIRED_SOURCE = Path("src/main/java/com/asef/fixture/Calculator.java")

    def detect(self, root: Path) -> JavaMavenProject:
        try:
            resolved = root.resolve(strict=True)
        except OSError as exc:
            raise JavaMavenProjectError("Java project root is unavailable") from exc
        if not resolved.is_dir() or root.is_symlink():
            raise JavaMavenProjectError("Java project root must be a regular directory")
        pom = resolved / "pom.xml"
        source = resolved / self._REQUIRED_SOURCE
        for value, label in ((pom, "pom.xml"), (source, "Calculator source")):
            if not value.is_file() or value.is_symlink():
                raise JavaMavenProjectError(f"{label} must be a regular non-symlink file")
        try:
            payload = pom.read_bytes()
        except OSError as exc:
            raise JavaMavenProjectError("pom.xml cannot be read") from exc
        if not 1 <= len(payload) <= 64 * 1024:
            raise JavaMavenProjectError("pom.xml is empty or oversized")
        upper = payload.upper()
        if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
            raise JavaMavenProjectError("pom.xml declarations and entities are forbidden")
        try:
            document = ET.fromstring(payload)
        except ET.ParseError as exc:
            raise JavaMavenProjectError("pom.xml is not valid XML") from exc
        if document.tag != "{http://maven.apache.org/POM/4.0.0}project":
            raise JavaMavenProjectError("pom.xml uses an unsupported root element")
        expected = {
            "groupId": "com.asef.fixture",
            "artifactId": "calculator",
            "version": "1.0.0",
        }
        for name, value in expected.items():
            if self._text(document, name) != value:
                raise JavaMavenProjectError(f"unsupported Maven {name}")
        release = self._text(document, "properties/maven.compiler.release")
        junit = self._text(document, "properties/junit.version")
        plugins = document.findall("m:build/m:plugins/m:plugin", self._NS)
        dependencies = document.findall("m:dependencies/m:dependency", self._NS)
        if len(plugins) != 1 or len(dependencies) != 1:
            raise JavaMavenProjectError("fixture requires exactly one plugin and one dependency")
        plugin = plugins[0]
        dependency = dependencies[0]
        if (
            self._child(plugin, "groupId") != "org.apache.maven.plugins"
            or self._child(plugin, "artifactId") != "maven-surefire-plugin"
            or self._child(plugin, "version") != "3.6.0"
        ):
            raise JavaMavenProjectError("unsupported Maven plugin")
        if (
            self._child(dependency, "groupId") != "org.junit.jupiter"
            or self._child(dependency, "artifactId") != "junit-jupiter"
            or self._child(dependency, "version") != "${junit.version}"
            or self._child(dependency, "scope") != "test"
        ):
            raise JavaMavenProjectError("unsupported Maven dependency")
        if document.find("m:repositories", self._NS) is not None or document.find("m:pluginRepositories", self._NS) is not None:
            raise JavaMavenProjectError("custom Maven repositories are forbidden")
        if release != "21" or junit != "5.13.4":
            raise JavaMavenProjectError("Java or JUnit version is outside the pinned fixture")
        return JavaMavenProject(resolved, pom, resolved / "src/main/java", release, junit, "3.6.0")

    def _text(self, root: ET.Element, path: str) -> str:
        node = root.find("/".join(f"m:{part}" for part in path.split("/")), self._NS)
        return "" if node is None or node.text is None else node.text.strip()

    def _child(self, root: ET.Element, name: str) -> str:
        node = root.find(f"m:{name}", self._NS)
        return "" if node is None or node.text is None else node.text.strip()
