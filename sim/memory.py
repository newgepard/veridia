from collections import defaultdict
from typing import Protocol


class MemoryStore(Protocol):
    def record(self, agent_id: str, round: int, event: dict) -> None: ...
    def recall(self, agent_id: str, query: str | None = None) -> list[dict]: ...


class InMemoryStore:
    def __init__(self) -> None:
        self._events: dict[str, list[dict]] = defaultdict(list)

    def record(self, agent_id: str, round: int, event: dict) -> None:
        self._events[agent_id].append({"round": round, **event})

    def recall(self, agent_id: str, query: str | None = None) -> list[dict]:
        return list(self._events.get(agent_id, []))
