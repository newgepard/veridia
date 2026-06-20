"""可预测性快检测试 —— 用 FakeLLM(脚本化 JSON),无 API key。

覆盖:accuracy 计算正确、不泄露未来帧、JSON 解析 fail-closed、无未来帧/不变样本被跳过。
约定:晶族=honest、雾族=manipulative。
"""
import json

from ca.predict_check import predict_check, predict_one, _actual_direction
from ca.state import HONEST, MANIPULATIVE
from llm.base import FakeLLM


def _frame(step: int, width: int, height: int, beliefs: dict) -> dict:
    """造一帧 dict。beliefs: {(x,y): belief}, 缺省 0.5。type 按 belief>=0.5 推。"""
    n = width * height
    belief = [0.5] * n
    typ = [HONEST] * n
    for (x, y), b in beliefs.items():
        i = y * width + x
        belief[i] = b
        typ[i] = HONEST if b >= 0.5 else MANIPULATIVE
    return {
        "step": step, "width": width, "height": height,
        "belief": belief, "type": typ, "standing": [0.5] * n,
    }


def _trace(frames: list[dict], F=None) -> dict:
    cfg = {"width": frames[0]["width"], "height": frames[0]["height"]}
    if F is not None:
        cfg["F"] = F
    return {"frames": frames, "config": cfg, "microscope": []}


def _resp(direction: str, reason: str = "r") -> str:
    return json.dumps({"direction": direction, "reason": reason})


# ---- accuracy 计算 ----

def test_accuracy_all_correct():
    # cell(0,0): belief 0.2 -> 0.8(变大=toward_truth);LLM 也答 toward_truth → 命中。
    frames = [
        _frame(0, 2, 2, {(0, 0): 0.2}),
        _frame(1, 2, 2, {(0, 0): 0.8}),
    ]
    trace = _trace(frames)
    llm = FakeLLM([_resp("toward_truth")])
    out = predict_check(trace, llm, "m", [(0, 0, 0)], k=1)
    assert out["accuracy"] == 1.0
    assert out["n"] == 1
    assert out["baseline"] == 0.5
    assert out["per_sample"][0]["actual"] == "toward_truth"
    assert out["per_sample"][0]["predicted"] == "toward_truth"
    assert out["per_sample"][0]["correct"] is True


def test_accuracy_half():
    # 两样本:一个命中、一个不命中 → accuracy 0.5。
    frames = [
        _frame(0, 2, 2, {(0, 0): 0.2, (1, 1): 0.8}),
        _frame(1, 2, 2, {(0, 0): 0.8, (1, 1): 0.2}),  # (0,0) 升,(1,1) 降
    ]
    trace = _trace(frames)
    # (0,0) actual=toward_truth,LLM 答对;(1,1) actual=toward_lie,LLM 答错(toward_truth)。
    llm = FakeLLM([_resp("toward_truth"), _resp("toward_truth")])
    out = predict_check(trace, llm, "m", [(0, 0, 0), (0, 1, 1)], k=1)
    assert out["n"] == 2
    assert out["accuracy"] == 0.5
    corrects = {(p["x"], p["y"]): p["correct"] for p in out["per_sample"]}
    assert corrects[(0, 0)] is True
    assert corrects[(1, 1)] is False


def test_actual_direction_sign():
    frames = [
        _frame(0, 2, 2, {(0, 0): 0.3, (1, 0): 0.7, (1, 1): 0.5}),
        _frame(1, 2, 2, {(0, 0): 0.9, (1, 0): 0.1, (1, 1): 0.5}),
    ]
    tr = _trace(frames)
    assert _actual_direction(tr, 0, 0, 0, 1) == "toward_truth"   # 0.3 -> 0.9
    assert _actual_direction(tr, 0, 1, 0, 1) == "toward_lie"     # 0.7 -> 0.1
    assert _actual_direction(tr, 0, 1, 1, 1) is None             # 0.5 -> 0.5 不变


# ---- 不泄露未来帧 ----

def test_no_future_leak_in_prompt():
    # 未来帧 belief 是一个独特数字,断言它绝不出现在喂给 LLM 的提示里。
    future_marker = 0.917001
    frames = [
        _frame(0, 2, 2, {(0, 0): 0.2}),
        _frame(1, 2, 2, {(0, 0): future_marker}),
    ]
    trace = _trace(frames, F={"proposition": "F", "truth_pole": "T", "lie_pole": "L"})
    llm = FakeLLM([_resp("toward_truth")])
    predict_check(trace, llm, "m", [(0, 0, 0)], k=1)
    assert len(llm.calls) == 1
    prompt = llm.calls[0]["system"] + "\n" + llm.calls[0]["user"]
    assert "0.917" not in prompt
    assert str(future_marker) not in prompt
    # 当前帧的 belief(0.2)应当在提示里(确实只喂了当前帧)。
    assert "0.2" in prompt


def test_predict_one_only_sees_current_cell_state():
    # predict_one 只接 cell_state,结构上无从看见未来——验证它不要求 trace。
    F = {"proposition": "F", "truth_pole": "T", "lie_pole": "L"}
    llm = FakeLLM([_resp("toward_lie")])
    out = predict_one(llm, "m", F, {"belief": 0.1, "type": MANIPULATIVE, "standing": 0.5})
    assert out["direction"] == "toward_lie"


# ---- fail-closed JSON 解析 ----

def test_fail_closed_garbage_json():
    frames = [
        _frame(0, 2, 2, {(0, 0): 0.2}),
        _frame(1, 2, 2, {(0, 0): 0.8}),
    ]
    trace = _trace(frames)
    llm = FakeLLM(["totally not json"])
    out = predict_check(trace, llm, "m", [(0, 0, 0)], k=1)
    # fail-closed 到 toward_truth;actual 恰好也是 toward_truth,但 reason 暴露它是 unparseable。
    assert out["n"] == 1
    assert out["per_sample"][0]["predicted"] == "toward_truth"
    assert "unparseable" in out["per_sample"][0]["reason"]


def test_fail_closed_invalid_direction():
    F = {"proposition": "F", "truth_pole": "T", "lie_pole": "L"}
    llm = FakeLLM([json.dumps({"direction": "sideways", "reason": "x"})])
    out = predict_one(llm, "m", F, {"belief": 0.9, "type": HONEST})
    assert out["direction"] == "toward_truth"
    assert "invalid direction" in out["reason"]


def test_fail_closed_missing_direction_key():
    F = {"proposition": "F", "truth_pole": "T", "lie_pole": "L"}
    llm = FakeLLM([json.dumps({"reason": "no direction here"})])
    out = predict_one(llm, "m", F, {"belief": 0.1, "type": MANIPULATIVE})
    assert out["direction"] == "toward_truth"
    assert "invalid direction" in out["reason"]


# ---- 跳过无真值样本 ----

def test_skips_samples_without_future_frame():
    # k=8 但只有 2 帧:没有 step_index+8 的帧 → 全跳过,n=0,不消耗 LLM 调用。
    frames = [
        _frame(0, 2, 2, {(0, 0): 0.2}),
        _frame(1, 2, 2, {(0, 0): 0.8}),
    ]
    trace = _trace(frames)
    llm = FakeLLM([])  # 不应被调用
    out = predict_check(trace, llm, "m", [(0, 0, 0)], k=8)
    assert out["n"] == 0
    assert out["accuracy"] == 0.0
    assert out["per_sample"] == []
    assert len(llm.calls) == 0


def test_skips_unchanged_belief_sample():
    # belief 不变(0.5 -> 0.5):无方向真值,跳过,不消耗 LLM。
    frames = [
        _frame(0, 2, 2, {(0, 0): 0.5}),
        _frame(1, 2, 2, {(0, 0): 0.5}),
    ]
    trace = _trace(frames)
    llm = FakeLLM([])
    out = predict_check(trace, llm, "m", [(0, 0, 0)], k=1)
    assert out["n"] == 0
    assert len(llm.calls) == 0


def test_skips_out_of_bounds_sample():
    frames = [
        _frame(0, 2, 2, {(0, 0): 0.2}),
        _frame(1, 2, 2, {(0, 0): 0.8}),
    ]
    trace = _trace(frames)
    llm = FakeLLM([_resp("toward_truth")])
    # 越界样本被跳过,只剩 (0,0,0) 有效。
    out = predict_check(trace, llm, "m", [(99, 0, 0), (0, 9, 9), (0, 0, 0)], k=1)
    assert out["n"] == 1
    assert out["per_sample"][0]["x"] == 0 and out["per_sample"][0]["y"] == 0


# ---- 烟雾测试:在真实 fixture trace 上跑,FakeLLM 永远答 toward_truth ----

def test_runs_on_fixture_shape_with_fake_llm():
    import os
    from ca.run import pick_samples
    path = os.path.join(os.path.dirname(__file__), "..", "web", "src",
                        "ca", "fixtures", "run-trace.json")
    with open(path) as f:
        trace = json.load(f)
    samples = pick_samples(trace, per_frame=3)
    # 给足够多的固定回答(每个有效样本一次)。
    llm = FakeLLM([_resp("toward_truth")] * len(samples))
    out = predict_check(trace, llm, "m", samples, k=8)
    assert out["baseline"] == 0.5
    assert out["n"] <= len(samples)
    assert 0.0 <= out["accuracy"] <= 1.0
    for p in out["per_sample"]:
        assert p["actual"] in ("toward_truth", "toward_lie")
        assert p["predicted"] in ("toward_truth", "toward_lie")
