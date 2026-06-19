from sim.memory import InMemoryStore


def test_record_and_recall_in_order():
    m = InMemoryStore()
    m.record("veridia", 1, {"saw": "umbra grabbed"})
    m.record("veridia", 2, {"saw": "umbra promised share"})
    m.record("umbra", 1, {"note": "veridia naive"})
    assert m.recall("veridia") == [
        {"round": 1, "saw": "umbra grabbed"},
        {"round": 2, "saw": "umbra promised share"},
    ]
    assert m.recall("umbra") == [{"round": 1, "note": "veridia naive"}]
    assert m.recall("nobody") == []
