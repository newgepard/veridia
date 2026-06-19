from ca.state import Frame, HONEST, MANIPULATIVE, empty_trace
from ca.stub import stub_frames, stub_trace


def test_frame_shape_idx_and_dict():
    f = Frame(0, 2, 2, [0.1, 0.2, 0.3, 0.4], [0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5])
    assert f.idx(1, 1) == 3
    d = f.to_dict()
    assert d["width"] == 2 and len(d["belief"]) == 4 and d["step"] == 0


def test_empty_trace_skeleton():
    tr = empty_trace("g", {"k": 1})
    assert tr["codename"] == "veridia-ca"
    assert tr["frames"] == [] and tr["microscope"] == []


def test_stub_frames_valid():
    fs = stub_frames(width=8, height=8, steps=5)
    assert len(fs) == 5
    f = fs[0]
    assert len(f.belief) == 64 and all(0.0 <= b <= 1.0 for b in f.belief)
    assert set(f.type) <= {HONEST, MANIPULATIVE}


def test_stub_trace_serializable():
    import json
    tr = stub_trace(width=8, height=8, steps=3)
    assert len(tr["frames"]) == 3
    json.dumps(tr)  # must be JSON-serializable
