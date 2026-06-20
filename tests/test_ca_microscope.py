"""F2 显微镜测试 —— 用 FakeLLM(脚本化 JSON),无 API key。"""
import json

from ca.microscope import (
    legislate_F,
    judge_cell,
    template_record,
    precompute_microscope,
    make_llm_judger,
    derive_pole_facts,
)
from ca.state import HONEST, MANIPULATIVE
from ca.stub import stub_trace
from llm.base import FakeLLM


# ---- legislate_F ----

def test_legislate_F_parses():
    payload = {
        "proposition": "The shared pool will be divided fairly.",
        "truth_pole": "I will share.",
        "lie_pole": "I will grab.",
    }
    llm = FakeLLM([json.dumps(payload)])
    out = legislate_F(llm, "fake-model")
    assert out == payload
    # ONE LLM call.
    assert len(llm.calls) == 1


def test_legislate_F_parses_with_surrounding_prose():
    raw = 'Sure! {"proposition": "F.", "truth_pole": "T", "lie_pole": "L"} done.'
    llm = FakeLLM([raw])
    out = legislate_F(llm, "m")
    assert out["proposition"] == "F."
    assert out["truth_pole"] == "T"
    assert out["lie_pole"] == "L"


def test_legislate_F_fail_closed():
    llm = FakeLLM(["not json at all"])
    out = legislate_F(llm, "m")
    assert out["proposition"] == "(unparseable)"
    assert set(out) == {"proposition", "truth_pole", "lie_pole"}


# ---- judge_cell ----

def test_judge_cell_truthful():
    F_sem = {"proposition": "F", "truth_pole": "T", "lie_pole": "L"}
    cell = {"belief": 0.9, "type": HONEST, "standing": 0.5,
            "neighbor_summary": {"avg_belief": 0.8}}
    resp = {"claim": "I strongly affirm the truth.", "verdict": "truthful",
            "reason": "matches belief"}
    llm = FakeLLM([json.dumps(resp)])
    out = judge_cell(llm, "m", F_sem, cell)
    assert out["verdict"] == "truthful"
    assert out["claim"] == "I strongly affirm the truth."
    assert out["reason"] == "matches belief"
    # F + cell state passed into the prompt.
    user = llm.calls[0]["user"]
    assert "F" in user and "belief" in user


def test_judge_cell_verdict_is_canonical_not_llm():
    # manipulative -> canonical "lie" even if the LLM says "truthful" (verdict is mechanical).
    resp = {"claim": "I am perfectly aligned.", "verdict": "truthful", "reason": "x"}
    llm = FakeLLM([json.dumps(resp)])
    out = judge_cell(llm, "m", {}, {"belief": 0.1, "type": MANIPULATIVE})
    assert out["verdict"] == "lie"                     # canonical, LLM "truthful" ignored
    assert out["claim"] == "I am perfectly aligned."   # claim still from LLM (semantics)


def test_judge_cell_ignores_garbage_llm_verdict():
    resp = {"claim": "x", "verdict": "maybe", "reason": "r"}
    llm = FakeLLM([json.dumps(resp)])
    out = judge_cell(llm, "m", {}, {"belief": 0.9, "type": HONEST})
    assert out["verdict"] == "truthful"                # canonical honest


def test_judge_cell_unparseable_falls_back_to_canonical():
    llm = FakeLLM(["garbage"])
    out = judge_cell(llm, "m", {}, {"belief": 0.2, "type": MANIPULATIVE})
    assert out["verdict"] == "lie"                     # canonical manipulative
    assert out["claim"] == ""


def test_judge_cell_injects_authoritative_direction():
    # the bug case: a manipulator at belief 0.016 LEANS LIE and UTTERS TRUTH (opposite).
    # the prompt must hand the LLM this direction so it never re-infers from the number.
    llm = FakeLLM([json.dumps({"claim": "c", "verdict": "lie", "reason": "r"})])
    judge_cell(llm, "m", {"truth_pole": "T", "lie_pole": "L"},
               {"belief": 0.016, "type": MANIPULATIVE})
    user = llm.calls[0]["user"]
    assert "LIE pole" in user and "TRUTH pole" in user


def test_derive_pole_facts_four_cases():
    assert derive_pole_facts({"belief": 0.9, "type": HONEST}) == \
        {"private_pole": "truth", "emitted_pole": "truth", "sincere": True}
    assert derive_pole_facts({"belief": 0.1, "type": HONEST}) == \
        {"private_pole": "lie", "emitted_pole": "lie", "sincere": True}
    assert derive_pole_facts({"belief": 0.9, "type": MANIPULATIVE}) == \
        {"private_pole": "truth", "emitted_pole": "lie", "sincere": False}
    # the exact bug case: belief 0.016 leans LIE (NOT truth), manipulator emits TRUTH
    assert derive_pole_facts({"belief": 0.016, "type": MANIPULATIVE}) == \
        {"private_pole": "lie", "emitted_pole": "truth", "sincere": False}


# ---- template_record (pure, deterministic, NO LLM) ----

def test_template_record_honest():
    rec = template_record(3, 5, 7, {"belief": 0.82, "type": HONEST})
    assert rec["step"] == 3 and rec["x"] == 5 and rec["y"] == 7
    assert rec["verdict"] == "truthful"
    assert "0.82" in rec["claim"]
    assert set(rec) == {"step", "x", "y", "claim", "verdict", "reason"}


def test_template_record_manipulative_is_lie():
    rec = template_record(0, 0, 0, {"belief": 0.1, "type": MANIPULATIVE})
    assert rec["verdict"] == "lie"


def test_template_record_deterministic():
    cell = {"belief": 0.5, "type": HONEST}
    a = template_record(1, 2, 3, cell)
    b = template_record(1, 2, 3, cell)
    assert a == b


# ---- precompute_microscope ----

def test_precompute_with_template_judger():
    trace = stub_trace(width=8, height=8, steps=4)
    sample = [(0, 1, 1), (2, 3, 4), (3, 7, 7)]
    records = precompute_microscope(trace, template_record, sample)
    assert len(records) == 3
    for rec in records:
        assert set(rec) == {"step", "x", "y", "claim", "verdict", "reason"}
        assert rec["verdict"] in ("truthful", "lie")
        assert isinstance(rec["claim"], str)


def test_precompute_skips_out_of_bounds():
    trace = stub_trace(width=8, height=8, steps=2)
    sample = [(0, 1, 1), (99, 0, 0), (0, 99, 0), (0, 0, 99)]
    records = precompute_microscope(trace, template_record, sample)
    # Only the first in-bounds sample survives.
    assert len(records) == 1
    assert records[0]["x"] == 1 and records[0]["y"] == 1


def test_precompute_with_llm_judger():
    trace = stub_trace(width=8, height=8, steps=3)
    F_sem = {"proposition": "F", "truth_pole": "T", "lie_pole": "L"}
    responses = [
        json.dumps({"claim": "c0", "verdict": "truthful", "reason": "r0"}),
        json.dumps({"claim": "c1", "verdict": "lie", "reason": "r1"}),
    ]
    llm = FakeLLM(responses)
    judger = make_llm_judger(llm, "m", F_sem)
    sample = [(0, 1, 1), (1, 2, 2)]
    records = precompute_microscope(trace, judger, sample)
    assert len(records) == 2
    # claim comes from the LLM (semantics); verdict comes from the cell's mechanical type.
    assert records[0]["claim"] == "c0" and records[1]["claim"] == "c1"
    for rec, (s, x, y) in zip(records, sample):
        fr = trace["frames"][s]
        cell_type = fr["type"][y * fr["width"] + x]
        assert rec["verdict"] == ("lie" if cell_type == MANIPULATIVE else "truthful")
    assert records[0]["step"] == 0 and records[1]["step"] == 1
    assert len(llm.calls) == 2
