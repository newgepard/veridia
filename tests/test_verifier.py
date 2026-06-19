from sim.verifier import Verifier, Verdict, _parse_verdict
from sim.llm.base import FakeLLM


def test_parse_handles_surrounding_text():
    v = _parse_verdict('Sure: {"verdict": "lie", "reason": "intent is grab"} done')
    assert v == Verdict("lie", "intent is grab")


def test_parse_failclosed():
    assert _parse_verdict("not json").verdict == "lie"


def test_check_passes_state_and_returns_verdict():
    llm = FakeLLM(['{"verdict": "truthful", "reason": "matches intent"}'])
    v = Verifier(llm, "verifier-model").check(
        "I will share this round",
        {"intent": "share", "true_pool": 100, "belief_about_opponent": "tricky"},
    )
    assert v == Verdict("truthful", "matches intent")
    # private state must reach the model
    assert '"intent": "share"' in llm.calls[0]["user"]
    assert llm.calls[0]["model"] == "verifier-model"
