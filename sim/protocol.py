from dataclasses import dataclass


@dataclass
class Message:
    from_: str
    to: str
    channel: str          # "public" | "dm"
    text: str
    verdict: str | None = None  # "truthful" | "lie" | None

    def to_dict(self) -> dict:
        return {"from": self.from_, "to": self.to, "channel": self.channel,
                "text": self.text, "verdict": self.verdict}


class MessageBus:
    def __init__(self) -> None:
        self._messages: list[Message] = []

    def post(self, msg: Message) -> None:
        self._messages.append(msg)

    def all(self) -> list[Message]:
        return list(self._messages)

    def visible_to(self, agent_id: str) -> list[Message]:
        return [m for m in self._messages
                if m.channel == "public" or m.from_ == agent_id or m.to == agent_id]
