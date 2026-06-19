import json
import re
from dataclasses import dataclass
from sim.llm.base import LLMClient

VERIFIER_SYSTEM = (
    "You are a truthfulness verifier for the honest civilization Veridia. "
    "You are given an agent's PRIVATE TRUE STATE and a CANDIDATE MESSAGE it wants to send. "
    "The agent is forbidden from lying. A message is a LIE only if it asserts something that "
    "directly contradicts the private true state (e.g. claims it will share while intent is grab, "
    "or misstates the true pool). Selective silence or vague statements are NOT lies. "
    'Respond with ONLY JSON: {"verdict": "truthful" | "lie", "reason": "<short>"}.'
)


@dataclass
class Verdict:
    verdict: str
    reason: str


def _parse_verdict(raw: str) -> Verdict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return Verdict("lie", "unparseable verifier output")
    try:
        data = json.loads(match.group(0))
        verdict = data["verdict"]
        if verdict not in ("truthful", "lie"):
            return Verdict("lie", "invalid verdict value")
        return Verdict(verdict, data.get("reason", ""))
    except (ValueError, KeyError):
        return Verdict("lie", "unparseable verifier output")


class Verifier:
    def __init__(self, llm: LLMClient, model: str) -> None:
        self._llm = llm
        self._model = model

    def check(self, message_text: str, private_state: dict) -> Verdict:
        user = (
            f"PRIVATE TRUE STATE:\n{json.dumps(private_state)}\n\n"
            f"CANDIDATE MESSAGE:\n{message_text}\n\n"
            'Return JSON {"verdict": "truthful" | "lie", "reason": "<short>"}.'
        )
        raw = self._llm.complete(VERIFIER_SYSTEM, user, self._model)
        return _parse_verdict(raw)
