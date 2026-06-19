import json
from sim.trace import TraceWriter


def test_trace_shape_and_write(tmp_path):
    tw = TraceWriter("g1", {"pool": 100, "rounds": 8})
    tw.add_round({"round": 1, "actions": {"veridia": "share", "umbra": "grab"}})
    tw.finalize("umbra", {"lie_count": 1})
    d = tw.as_dict()
    assert d["game_id"] == "g1"
    assert d["codename"] == "veridia"
    assert d["winner"] == "umbra"
    assert d["rounds"][0]["round"] == 1
    assert d["metrics"]["lie_count"] == 1

    out = tmp_path / "t.json"
    tw.write(str(out))
    assert json.loads(out.read_text())["winner"] == "umbra"
