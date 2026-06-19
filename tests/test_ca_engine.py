"""F1 测试:CA 引擎跑得动、帧形状对、belief 在 [0,1]、结构活着(非平/非爆)。"""
import math

import numpy as np

from ca.engine import CAEngine
from ca.state import Frame, HONEST, MANIPULATIVE
from ca.lenia import LeniaParams, make_kernel, lenia_step, seed_orbium, growth


def test_engine_runs_50_steps_no_error():
    eng = CAEngine(width=64, height=64, seed=7)
    for _ in range(50):
        eng.step()
    assert eng.step_count == 50


def test_frame_shapes_valid():
    w, h = 48, 40
    eng = CAEngine(width=w, height=h, seed=1)
    eng.step()
    f = eng.frame()
    assert isinstance(f, Frame)
    assert f.width == w and f.height == h
    assert len(f.belief) == w * h
    assert len(f.type) == w * h
    assert len(f.standing) == w * h
    assert f.step == 1
    # 索引帮手与扁平化一致
    assert f.idx(3, 2) == 2 * w + 3


def test_belief_stays_in_unit_interval():
    eng = CAEngine(width=64, height=64, seed=3)
    for _ in range(50):
        eng.step()
    f = eng.frame()
    assert min(f.belief) >= 0.0
    assert max(f.belief) <= 1.0
    # standing 也守 [0,1]
    assert min(f.standing) >= 0.0 and max(f.standing) <= 1.0
    # type 只有两个合法值
    assert set(f.type) <= {HONEST, MANIPULATIVE}


def test_structure_is_alive_not_flat_not_exploded():
    """50 步后 belief 既不均匀(有结构)也不爆炸/NaN。"""
    eng = CAEngine(width=64, height=64, seed=5)
    for _ in range(50):
        eng.step()
    arr = np.array(eng.frame().belief, dtype=np.float64)
    # 有限(没 NaN/inf)
    assert np.all(np.isfinite(arr))
    # 有结构:方差高于一个小阈值(不是平的)
    var = float(arr.var())
    assert var > 1e-4, f"belief 太平,var={var}"
    # 没爆:仍在 [0,1]
    assert arr.min() >= 0.0 and arr.max() <= 1.0


def test_deterministic_given_seed():
    a = CAEngine(width=48, height=48, seed=42)
    b = CAEngine(width=48, height=48, seed=42)
    for _ in range(10):
        a.step()
        b.step()
    assert a.frame().to_dict() == b.frame().to_dict()


def test_different_seeds_differ():
    a = CAEngine(width=48, height=48, seed=1)
    b = CAEngine(width=48, height=48, seed=2)
    for _ in range(5):
        a.step()
        b.step()
    assert a.frame().to_dict() != b.frame().to_dict()


def test_no_llm_import_in_engine():
    """LITMUS:引擎/规则/Lenia 三模块的模块树里没有 LLM 依赖。"""
    import ca.engine
    import ca.rule
    import ca.lenia
    import sys
    suspects = ("anthropic", "openai", "sim.llm")
    # 确认这些模块没把任一 LLM 实现拉进来(它们不 import sim.llm 等)
    for mod in (ca.engine, ca.rule, ca.lenia):
        src = mod.__file__
        with open(src, "r", encoding="utf-8") as fh:
            text = fh.read()
        for s in suspects:
            assert s not in text, f"{mod.__name__} 含 LLM 引用 {s}"


def test_lenia_step_keeps_unit_interval_and_finite():
    p = LeniaParams()
    k = make_kernel(p)
    grid = seed_orbium(64, 64)
    for _ in range(20):
        grid = lenia_step(grid, p, k)
    assert np.all(np.isfinite(grid))
    assert grid.min() >= 0.0 and grid.max() <= 1.0


def test_lenia_kernel_normalized_and_ring():
    p = LeniaParams()
    k = make_kernel(p)
    # 归一化
    assert math.isclose(k.sum(), 1.0, rel_tol=1e-9)
    # 环形:中心(R,R)处权重应低于环上的峰值
    R = p.R
    center = k[R, R]
    assert center < k.max()


def test_growth_function_bounded():
    p = LeniaParams()
    x = np.linspace(0.0, 1.0, 101)
    g = growth(x, p)
    assert g.min() >= -1.0 - 1e-9 and g.max() <= 1.0 + 1e-9


def test_orbium_glides_not_static():
    """Orbium 在自身参数下应移动(质心位移),证明是会动的"生物"而非静态斑块。"""
    p = LeniaParams()
    k = make_kernel(p)
    grid = seed_orbium(80, 80, cx=40, cy=40)

    def centroid(g):
        ys, xs = np.mgrid[0:g.shape[0], 0:g.shape[1]]
        tot = g.sum()
        return (xs * g).sum() / tot, (ys * g).sum() / tot

    c0 = centroid(grid)
    for _ in range(40):
        grid = lenia_step(grid, p, k)
    # 仍是活的结构(没死成 0)
    assert grid.sum() > 1.0
    c1 = centroid(grid)
    moved = math.hypot(c1[0] - c0[0], c1[1] - c0[1])
    assert moved > 0.5, f"Orbium 没动 moved={moved}"
