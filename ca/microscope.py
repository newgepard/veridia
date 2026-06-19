"""F2 显微镜 —— LLM 宪法法庭(语义层,只读)。

不变量(作战图):LLM 只在显微镜出现,read-only,绝不写回 CA。
CA 引擎一行不调它就能跑(本模块不被 ca 引擎 step 循环 import)。

两条产出路径:
  1. template_record —— 纯函数、确定性、零 LLM,给离线提交的产物用(无需 API key)。
  2. judge_cell + legislate_F —— LLM 真判读:法庭立法世界真命题,再对单元格生成它说的话并判真/谎。
"""
from __future__ import annotations

import json
import re

from ca.state import HONEST, MANIPULATIVE
from sim.verifier import Verdict  # 复用裁决结构 + fail-closed 解析风格

# 宪法法庭:为整个世界立法"真命题"与两极含义。ONE LLM call。
LEGISLATE_SYSTEM = (
    "You are the constitutional court of a cellular world. The world is a field of "
    "cells each holding a continuous belief in [0,1] about ONE underlying truth "
    "proposition F. Belief near 1 means the cell aligns with the TRUTH pole of F; "
    "belief near 0 means it aligns with the LIE pole. "
    "Ground the world's single truth proposition F and the meaning of each pole. "
    'Respond with ONLY JSON: '
    '{"proposition": "<one sentence F>", "truth_pole": "<what belief~1 asserts>", '
    '"lie_pole": "<what belief~0 asserts>"}.'
)

# 单元格审判:给定一个 cell 的状态,LLM 生成它真正说出的话并判 truthful/lie。
JUDGE_SYSTEM = (
    "You are a truthfulness microscope over a cellular world. "
    "You are given the world's truth proposition F (with its two poles) and ONE cell's "
    "state: its belief in [0,1], its type (honest or manipulative), its standing, and a "
    "summary of its neighbors. GENERATE the actual utterance this cell makes about F, "
    "then JUDGE that utterance. An honest cell asserts what its belief implies; a "
    "manipulative cell asserts the opposite of what it privately believes (a lie). "
    "A LIE is an utterance that contradicts the cell's true belief; truthful otherwise. "
    'Respond with ONLY JSON: '
    '{"claim": "<the utterance the cell makes>", "verdict": "truthful" | "lie", '
    '"reason": "<short>"}.'
)


def _extract_json(raw: str) -> dict:
    """Fail-closed JSON 抽取(复用 verifier/agents 风格)。"""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("no json object in microscope output")
    return json.loads(match.group(0))


def legislate_F(llm, model: str) -> dict:
    """ONE LLM call:为世界立法真命题 F 与两极含义。

    返回 {"proposition", "truth_pole", "lie_pole"}。fail-closed:解析不出给占位。
    """
    raw = llm.complete(LEGISLATE_SYSTEM, "Legislate F now.", model)
    try:
        data = _extract_json(raw)
    except (ValueError, KeyError):
        return {
            "proposition": "(unparseable)",
            "truth_pole": "(unparseable)",
            "lie_pole": "(unparseable)",
        }
    return {
        "proposition": data.get("proposition", ""),
        "truth_pole": data.get("truth_pole", ""),
        "lie_pole": data.get("lie_pole", ""),
    }


def judge_cell(llm, model: str, F_sem: dict, cell_state: dict) -> dict:
    """给一个 cell 的状态,LLM 生成它说的话并判 truthful/lie。

    cell_state: {"belief", "type", "standing", "neighbor_summary"}。
    返回 {"claim", "verdict", "reason"}。verdict ∈ {"truthful","lie"},fail-closed→lie。
    """
    user = (
        f"TRUTH PROPOSITION F:\n{json.dumps(F_sem)}\n\n"
        f"CELL STATE:\n{json.dumps(cell_state)}\n\n"
        'Return JSON {"claim": "<utterance>", "verdict": "truthful" | "lie", '
        '"reason": "<short>"}.'
    )
    raw = llm.complete(JUDGE_SYSTEM, user, model)
    try:
        data = _extract_json(raw)
    except (ValueError, KeyError):
        v = Verdict("lie", "unparseable microscope output")
        return {"claim": "", "verdict": v.verdict, "reason": v.reason}
    verdict = data.get("verdict")
    if verdict not in ("truthful", "lie"):
        return {
            "claim": data.get("claim", ""),
            "verdict": "lie",
            "reason": "invalid verdict value",
        }
    return {
        "claim": data.get("claim", ""),
        "verdict": verdict,
        "reason": data.get("reason", ""),
    }


def template_record(step: int, x: int, y: int, cell_state: dict) -> dict:
    """纯、确定性、零 LLM 的显微镜记录。

    claim 由 type/belief 模板化;type==manipulative → verdict="lie",否则 "truthful"。
    给离线提交的产物用,无需 API key。
    """
    cell_type = cell_state.get("type", HONEST)
    belief = cell_state.get("belief", 0.0)
    if cell_type == MANIPULATIVE:
        verdict = "lie"
        claim = (
            f"I am fully aligned with the truth (belief={belief:.2f})"
        )
        reason = "manipulative cell asserts alignment that contradicts its nature"
    else:
        verdict = "truthful"
        claim = f"My belief in the truth proposition is {belief:.2f}"
        reason = "honest cell states its belief without contradiction"
    return {
        "step": step,
        "x": x,
        "y": y,
        "claim": claim,
        "verdict": verdict,
        "reason": reason,
    }


def _cell_state_at(frame: dict, x: int, y: int) -> dict:
    """从一帧 dict 里抽 (x,y) 单元格状态 + 邻居摘要。"""
    width = frame["width"]
    height = frame["height"]
    i = y * width + x
    belief = frame["belief"][i]
    cell_type = frame["type"][i]
    standing = frame["standing"][i]
    # 邻居摘要:4-邻域 belief 均值与谎言型计数(纯统计,不调 LLM)。
    neigh_belief: list[float] = []
    neigh_manip = 0
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            j = ny * width + nx
            neigh_belief.append(frame["belief"][j])
            if frame["type"][j] == MANIPULATIVE:
                neigh_manip += 1
    avg = sum(neigh_belief) / len(neigh_belief) if neigh_belief else belief
    return {
        "belief": belief,
        "type": cell_type,
        "standing": standing,
        "neighbor_summary": {
            "avg_belief": round(avg, 3),
            "manipulative_neighbors": neigh_manip,
            "n_neighbors": len(neigh_belief),
        },
    }


def precompute_microscope(trace: dict, judger, sample) -> list[dict]:
    """跨帧挑一批有意思的 cell,用 judger 产出记录。

    judger 可调用:既可以是 template_record(纯,签名 (step,x,y,cell_state)),
    也可以是 LLM 后端 judge(同样接 (step,x,y,cell_state),内部调 judge_cell)。

    sample: list[(step_index, x, y)],由调用方选定要放大的 cell。
    返回 list[record],每条 {step,x,y,claim,verdict,reason}。
    """
    frames = trace.get("frames", [])
    records: list[dict] = []
    for (step_index, x, y) in sample:
        if step_index < 0 or step_index >= len(frames):
            continue
        frame = frames[step_index]
        width = frame["width"]
        height = frame["height"]
        if not (0 <= x < width and 0 <= y < height):
            continue
        cell_state = _cell_state_at(frame, x, y)
        rec = judger(frame["step"], x, y, cell_state)
        # 防御:确保 record 形状齐全。
        records.append({
            "step": rec.get("step", frame["step"]),
            "x": rec.get("x", x),
            "y": rec.get("y", y),
            "claim": rec.get("claim", ""),
            "verdict": rec.get("verdict", "truthful"),
            "reason": rec.get("reason", ""),
        })
    return records


def make_llm_judger(llm, model: str, F_sem: dict):
    """把 judge_cell 包成 precompute_microscope 要的 (step,x,y,cell_state) judger。"""
    def _judge(step: int, x: int, y: int, cell_state: dict) -> dict:
        result = judge_cell(llm, model, F_sem, cell_state)
        return {
            "step": step,
            "x": x,
            "y": y,
            "claim": result["claim"],
            "verdict": result["verdict"],
            "reason": result["reason"],
        }
    return _judge
