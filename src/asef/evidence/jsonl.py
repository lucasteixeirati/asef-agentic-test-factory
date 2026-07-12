from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(slots=True, frozen=True)
class Event:
    run_id: str
    event_type: str
    status: str
    payload: dict[str, Any]
    event_id: str = ""
    timestamp: str = ""
    schema_version: str = "1.0.0"

    def normalized(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_id"] = self.event_id or str(uuid4())
        data["timestamp"] = self.timestamp or datetime.now(UTC).isoformat()
        return data


class JsonlEventSink:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: Event) -> None:
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event.normalized(), ensure_ascii=False, sort_keys=True))
            stream.write("\n")
