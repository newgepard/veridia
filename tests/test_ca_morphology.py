"""Q7 形态学测试:连通域计数、dominant_type 分类、activity 死场=0、真 trace 跑通。"""
import json
import os

import numpy as np

from ca.state import HONEST, MANIPULATIVE
from ca.morphology import (
    label_structures,
    taxonomy,
    activity_series,
    summarize,
    TRUTH_CREATURE,
    LIE_CREATURE,
    MIXED,
)


def _frame(belief2d, type2d, step=0):
    """构造一个契约 Frame dict(并行数组,行优先)。"""
    belief = np.asarray(belief2d, dtype=np.float64)
    type_ = np.asarray(type2d, dtype=np.int64)
    h, w = belief.shape
    return {
        "step": step,
        "width": w,
        "height": h,
        "belief": belief.reshape(-1).tolist(),
        "type": type_.reshape(-1).tolist(),
        "standing": [0.5] * (w * h),
    }


def test_two_separated_structures_counted():
    """对角分离的两块(8-连通也不相连)应数到 2 个结构。"""
    H = HONEST
    belief = [
        [0.9, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.9],
        [0.0, 0.0, 0.9, 0.9],
    ]
    type2d = [[H] * 4 for _ in range(4)]
    structs = label_structures(_frame(belief, type2d), thresh=0.5)
    assert len(structs) == 2
    sizes = sorted(s["size"] for s in structs)
    assert sizes == [1, 3]


def test_diagonal_is_8_connected():
    """8-连通:对角相邻的两格算同一个结构。"""
    H = HONEST
    belief = [
        [0.9, 0.0],
        [0.0, 0.9],
    ]
    structs = label_structures(_frame(belief, [[H, H], [H, H]]), thresh=0.5)
    assert len(structs) == 1
    assert structs[0]["size"] == 2


def test_dominant_type_truth_lie_mixed():
    """dominant_type 按结构内 honest/manipulative 多数分类。"""
    H, M = HONEST, MANIPULATIVE
    # 全亮的 1x3 横条,类型决定分类
    belief = [[0.9, 0.9, 0.9]]

    truth = label_structures(_frame(belief, [[H, H, M]]), thresh=0.5)
    assert len(truth) == 1 and truth[0]["dominant_type"] == TRUTH_CREATURE

    lie = label_structures(_frame(belief, [[M, M, H]]), thresh=0.5)
    assert len(lie) == 1 and lie[0]["dominant_type"] == LIE_CREATURE

    # 1x2 平局 → mixed
    mixed = label_structures(_frame([[0.9, 0.9]], [[H, M]]), thresh=0.5)
    assert len(mixed) == 1 and mixed[0]["dominant_type"] == MIXED


def test_centroid_and_mean_belief():
    """质心与平均 belief 计算正确。"""
    H = HONEST
    belief = [
        [0.6, 0.8],
        [0.0, 0.0],
    ]
    structs = label_structures(_frame(belief, [[H, H], [H, H]]), thresh=0.5)
    assert len(structs) == 1
    s = structs[0]
    cx, cy = s["centroid"]
    assert abs(cx - 0.5) < 1e-9   # x: (0+1)/2
    assert abs(cy - 0.0) < 1e-9   # y: 都在第 0 行
    assert abs(s["mean_belief"] - 0.7) < 1e-9


def test_threshold_excludes_dim_cells():
    """低于阈值的格子不计入。"""
    H = HONEST
    belief = [[0.4, 0.4], [0.4, 0.4]]
    structs = label_structures(_frame(belief, [[H, H], [H, H]]), thresh=0.5)
    assert structs == []


def test_taxonomy_counts_and_coverage():
    """taxonomy 汇总数量与覆盖格子数。"""
    H, M = HONEST, MANIPULATIVE
    # 左上 truth 块(2格,honest),右下 lie 块(1格,manip)
    belief = [
        [0.9, 0.9, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.9],
    ]
    type2d = [
        [H, H, H],
        [H, H, H],
        [H, H, M],
    ]
    tax = taxonomy(_frame(belief, type2d), thresh=0.5)
    assert tax["n_structures"] == 2
    assert tax["counts"][TRUTH_CREATURE] == 1
    assert tax["counts"][LIE_CREATURE] == 1
    assert tax["counts"][MIXED] == 0
    assert tax["coverage"][TRUTH_CREATURE] == 2
    assert tax["coverage"][LIE_CREATURE] == 1
    assert tax["total_coverage"] == 3


def test_activity_dead_field_is_zero():
    """死场(逐帧 belief 不变)→ activity 全 0。"""
    H = HONEST
    f = _frame([[0.9, 0.0], [0.0, 0.9]], [[H, H], [H, H]])
    trace = {"frames": [dict(f, step=0), dict(f, step=1), dict(f, step=2)]}
    act = activity_series(trace)
    assert act == [0.0, 0.0]


def test_activity_detects_change():
    """场有变化 → activity 大于 0,值等于平均逐格绝对差。"""
    H = HONEST
    f0 = _frame([[0.0, 0.0], [0.0, 0.0]], [[H, H], [H, H]], step=0)
    f1 = _frame([[1.0, 0.0], [0.0, 0.0]], [[H, H], [H, H]], step=1)
    act = activity_series({"frames": [f0, f1]})
    assert len(act) == 1
    assert abs(act[0] - 0.25) < 1e-9   # 一格变 1.0,4 格平均


def test_activity_too_few_frames():
    assert activity_series({"frames": []}) == []
    H = HONEST
    one = _frame([[0.9]], [[H]])
    assert activity_series({"frames": [one]}) == []


def test_summarize_on_real_trace():
    """真 trace 跑通,且末帧结构数 > 0(Lenia 生物活着)。"""
    path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "web", "src", "ca", "fixtures", "run-trace.json"
    ))
    with open(path, "r", encoding="utf-8") as fh:
        trace = json.load(fh)

    summary = summarize(trace)
    assert summary["n_frames"] == len(trace["frames"])
    assert len(summary["per_frame"]) == summary["n_frames"]
    # activity 序列比帧数少 1
    assert len(summary["activity"]) == max(0, summary["n_frames"] - 1)
    # 末帧确实有涌现结构
    assert summary["last_frame_structures"] > 0
    # activity 非全 0(场是活的,非死场)
    assert any(a > 0 for a in summary["activity"])


def test_no_llm_import_in_morphology():
    """LITMUS:morphology 模块源码不含任何 LLM 引用。"""
    import ca.morphology
    with open(ca.morphology.__file__, "r", encoding="utf-8") as fh:
        text = fh.read()
    for s in ("anthropic", "openai", "import llm", "from llm"):
        assert s not in text, f"morphology 含 LLM 引用 {s}"
