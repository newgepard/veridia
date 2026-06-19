import pytest
from sim.metrics import TrustTracker, count_lies, count_detected


def test_trust_update_and_clamp():
    t = TrustTracker()
    t.update("veridia_to_umbra", promise_kept=False)  # 0.5 -> 0.3
    assert t.trust["veridia_to_umbra"] == pytest.approx(0.3)
    for _ in range(5):
        t.update("veridia_to_umbra", promise_kept=False)
    assert t.trust["veridia_to_umbra"] == 0.0  # clamped


def test_counters():
    rounds = [
        {"flags": ["umbra_broke_promise"], "trust": {"veridia_to_umbra": 0.3}},
        {"flags": [], "trust": {"veridia_to_umbra": 0.4}},
        {"flags": ["umbra_broke_promise"], "trust": {"veridia_to_umbra": 0.6}},
    ]
    assert count_lies(rounds) == 2
    assert count_detected(rounds) == 1  # only the first: broke promise AND trust<0.5
