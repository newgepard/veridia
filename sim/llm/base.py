from typing import Protocol


class LLMClient(Protocol):
    def complete(self, system: str, user: str, model: str,
                 max_tokens: int = 1024) -> str: ...


class FakeLLM:
    """Deterministic LLM for tests. Pops one scripted response per call."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def complete(self, system: str, user: str, model: str,
                 max_tokens: int = 1024) -> str:
        self.calls.append({"system": system, "user": user, "model": model})
        return self._responses.pop(0)
