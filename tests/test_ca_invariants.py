"""CA 不变量守卫层(project-guard-layer 思路:软纪律→硬守卫)。

把 v0.2 所有"承重保证"集中成自动失败的守卫,即使和单测有重叠也保留——
这是显式的护栏。任何改动碰穿其一,这里红。
"""
import math
import pathlib

import numpy as np
import pytest

from ca.engine import CAEngine
from ca.state import HONEST, MANIPULATIVE
from ca.microscope import template_record, legislate_F
from ca import run as ca_run

REPO = pathlib.Path(__file__).resolve().parent.parent

# 与 web/src/ca/types.ts 的 Frame 镜像一致(集成点契约)。
WEB_FRAME_KEYS = {"step", "width", "height", "belief", "type", "standing"}
MICRO_RECORD_KEYS = {"step", "x", "y", "claim", "verdict", "reason"}


# ── 守卫 1:帧状态契约(后端 Frame == 前端 types.ts Frame)──
def test_guard_frame_contract_matches_web_types():
    d = CAEngine(16, 16, seed=1).frame().to_dict()
    assert set(d) == WEB_FRAME_KEYS
    assert len(d["belief"]) == len(d["type"]) == len(d["standing"]) == 16 * 16


# ── 守卫 2:值域(belief/standing∈[0,1]、type⊆{0,1}、全有限)整局成立 ──
def test_guard_value_domains_over_a_run():
    eng = CAEngine(32, 32, seed=2)
    for _ in range(40):
        eng.step()
        f = eng.frame()
        assert all(0.0 <= b <= 1.0 and math.isfinite(b) for b in f.belief)
        assert all(0.0 <= s <= 1.0 and math.isfinite(s) for s in f.standing)
        assert set(f.type) <= {HONEST, MANIPULATIVE}


# ── 守卫 3:litmus —— CA 句法层零 LLM,关掉 LLM 也能跑(自然神论缺席循环)──
@pytest.mark.parametrize("mod", ["ca/engine.py", "ca/lenia.py", "ca/rule.py"])
def test_guard_litmus_ca_has_no_llm(mod):
    src = (REPO / mod).read_text()
    for forbidden in ("anthropic", "openai", "llm", "import microscope", "from ca.microscope"):
        assert forbidden not in src, f"{mod} 触碰了 LLM:{forbidden}"


# ── 守卫 4:结构活着(涌现,非死平/非爆炸)= 复杂科学,不是扩散 ──
def test_guard_structure_is_alive():
    eng = CAEngine(32, 32, seed=3)
    for _ in range(40):
        eng.step()
    var = float(np.var(np.array(eng.frame().belief)))
    assert var > 1e-4, "belief 场太平,结构死了(退回扩散)"
    assert math.isfinite(var)


# ── 守卫 5:确定性(同 seed 同帧)──
def test_guard_deterministic_given_seed():
    a = CAEngine(32, 32, seed=9)
    b = CAEngine(32, 32, seed=9)
    for _ in range(15):
        a.step(); b.step()
    assert a.frame().to_dict() == b.frame().to_dict()


# ── 守卫 6:trace 形状(== web CATrace)──
def test_guard_trace_shape():
    cfg = {"width": 32, "height": 32, "steps": 6, "seed": 4, "stride": 2, "round_dp": 3}
    tr = ca_run.build_trace(cfg)
    assert set(tr) >= {"game_id", "codename", "config", "frames", "microscope"}
    assert tr["codename"] == "veridia-ca"
    assert len(tr["frames"]) >= 1
    assert set(tr["frames"][0]) == WEB_FRAME_KEYS


# ── 守卫 7:集成点 —— 显微镜记录形状 == web MicroscopeRecord ──
def test_guard_microscope_record_shape():
    rec = template_record(2, 3, 4, {"belief": 0.1, "type": MANIPULATIVE})
    assert set(rec) == MICRO_RECORD_KEYS
    assert rec["verdict"] in ("truthful", "lie")


# ── 守卫 8:deism —— 创世立法 F 这条线接着(神在创世,非无神)──
def test_guard_deism_legislate_wired():
    # microscope 暴露 legislate_F(神能立法)
    assert callable(legislate_F)
    # run.py 的 --live 创世路径确实调 legislate_F(不是裸数字)
    run_src = (REPO / "ca/run.py").read_text()
    assert "legislate_F" in run_src, "创世没调 legislate_F → 退回无神"
