"""Q7 形态学指标(作战图 §5:盯形态学,不盯流行病学曲线)。

给"涌现生物"做可量化的分类学 + 混沌边缘判据。纯 numpy,**绝不 import LLM**
(守 litmus,与 ca.engine / ca.rule / ca.lenia 同一纪律)。

核心抽象:
- 一帧的 belief 场是连续场;对 belief>thresh 的格子做 8-连通连通域标注,
  每个连通域就是一只"涌现生物"(结构)。
- 按结构覆盖的格子里 honest/manipulative 多数,给生物分类:
  晶族(honest/水晶的晶)多数 → truth_creature;
  雾族(manipulative/起雾的雾)多数 → lie_creature;两者持平 → mixed。
- 混沌边缘代理:逐帧 belief 的平均逐格变化。全 0=死(凝固),过大=混沌,
  持续中等=生命/混沌边缘(edge of chaos)。

连通域标注自己实现 BFS(不依赖 scipy),8-邻域。
"""
from __future__ import annotations

import json
import os

import numpy as np

from ca.state import HONEST, MANIPULATIVE

# 分类标签(沿用晶族=honest、雾族=manipulative 框架)
TRUTH_CREATURE = "truth_creature"   # 晶族多数(水晶的晶)
LIE_CREATURE = "lie_creature"       # 雾族多数(起雾的雾)
MIXED = "mixed"                     # 两族持平


def _frame_arrays(frame: dict) -> tuple[np.ndarray, np.ndarray, int, int]:
    """把契约 Frame(dict,并行数组)还原成 (belief2d, type2d, w, h)。"""
    w = int(frame["width"])
    h = int(frame["height"])
    belief = np.asarray(frame["belief"], dtype=np.float64).reshape(h, w)
    type_ = np.asarray(frame["type"], dtype=np.int64).reshape(h, w)
    return belief, type_, w, h


def label_structures(frame: dict, thresh: float = 0.5) -> list[dict]:
    """对 belief>thresh 做 8-连通 flood-fill 连通域标注(自实现 BFS,不依赖 scipy)。

    返回结构列表,每个结构:
      {size, centroid: (x, y), mean_belief, dominant_type}
    dominant_type 按结构覆盖格子里 honest/manipulative 多数判定。
    """
    belief, type_, w, h = _frame_arrays(frame)
    active = belief > thresh                 # bool 掩码:哪些格子"亮着"
    visited = np.zeros((h, w), dtype=bool)

    # 8-邻域偏移
    nbrs = [(-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)]

    structures: list[dict] = []

    for sy in range(h):
        for sx in range(w):
            if not active[sy, sx] or visited[sy, sx]:
                continue
            # 从 (sx, sy) 起 BFS 收一整个连通域
            cells: list[tuple[int, int]] = []
            queue = [(sy, sx)]
            visited[sy, sx] = True
            head = 0
            while head < len(queue):
                cy, cx = queue[head]
                head += 1
                cells.append((cx, cy))
                for dy, dx in nbrs:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and active[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        queue.append((ny, nx))

            size = len(cells)
            xs = np.array([c[0] for c in cells], dtype=np.float64)
            ys = np.array([c[1] for c in cells], dtype=np.float64)
            beliefs = np.array([belief[c[1], c[0]] for c in cells], dtype=np.float64)
            types = np.array([type_[c[1], c[0]] for c in cells], dtype=np.int64)

            n_honest = int(np.count_nonzero(types == HONEST))
            n_manip = int(np.count_nonzero(types == MANIPULATIVE))
            if n_honest > n_manip:
                dominant = TRUTH_CREATURE
            elif n_manip > n_honest:
                dominant = LIE_CREATURE
            else:
                dominant = MIXED

            structures.append({
                "size": size,
                "centroid": (float(xs.mean()), float(ys.mean())),
                "mean_belief": float(beliefs.mean()),
                "dominant_type": dominant,
            })

    return structures


def taxonomy(frame: dict, thresh: float = 0.5) -> dict:
    """统计该帧 truth_creature / lie_creature / mixed 的数量与总覆盖(格子数)。"""
    structs = label_structures(frame, thresh=thresh)
    counts = {TRUTH_CREATURE: 0, LIE_CREATURE: 0, MIXED: 0}
    coverage = {TRUTH_CREATURE: 0, LIE_CREATURE: 0, MIXED: 0}
    for s in structs:
        d = s["dominant_type"]
        counts[d] += 1
        coverage[d] += s["size"]
    return {
        "n_structures": len(structs),
        "counts": counts,
        "coverage": coverage,
        "total_coverage": sum(coverage.values()),
    }


def activity_series(trace: dict) -> list[float]:
    """逐帧 mean(|belief_t - belief_{t-1}|),作混沌边缘代理。

    全 0=死(凝固),过大=混沌,持续中等=生命/混沌边缘。
    长度 = len(frames) - 1(首帧无前驱);frames<2 时返回 []。
    """
    frames = trace.get("frames", [])
    if len(frames) < 2:
        return []
    series: list[float] = []
    prev = np.asarray(frames[0]["belief"], dtype=np.float64)
    for f in frames[1:]:
        cur = np.asarray(f["belief"], dtype=np.float64)
        series.append(float(np.abs(cur - prev).mean()))
        prev = cur
    return series


def summarize(trace: dict, thresh: float = 0.5) -> dict:
    """综合:每帧 taxonomy + activity 序列 + 末帧结构数。"""
    frames = trace.get("frames", [])
    per_frame = [
        {"step": int(f.get("step", i)), **taxonomy(f, thresh=thresh)}
        for i, f in enumerate(frames)
    ]
    activity = activity_series(trace)
    last_n = per_frame[-1]["n_structures"] if per_frame else 0
    return {
        "n_frames": len(frames),
        "per_frame": per_frame,
        "activity": activity,
        "last_frame_structures": last_n,
    }


def _default_trace_path() -> str:
    return os.path.join(
        os.path.dirname(__file__), "..", "web", "src", "ca", "fixtures", "run-trace.json"
    )


def main() -> None:
    """CLI:读 web/src/ca/fixtures/run-trace.json 打印形态学摘要。"""
    path = os.path.abspath(_default_trace_path())
    with open(path, "r", encoding="utf-8") as f:
        trace = json.load(f)

    summary = summarize(trace)
    act = summary["activity"]
    print(f"trace: {path}")
    print(f"frames: {summary['n_frames']}  last_frame_structures: {summary['last_frame_structures']}")

    if act:
        arr = np.array(act, dtype=np.float64)
        # 混沌边缘判读:全静=死、过大=混沌、中等=边缘
        mean_a = float(arr.mean())
        if mean_a < 1e-6:
            verdict = "死场(凝固,activity≈0)"
        elif mean_a > 0.1:
            verdict = "混沌(activity 过大)"
        else:
            verdict = "混沌边缘/活(activity 中等)"
        print(f"activity: mean={mean_a:.5f} min={arr.min():.5f} max={arr.max():.5f} → {verdict}")

    print("\nper-frame taxonomy (step | truth/lie/mixed structs | total coverage):")
    for pf in summary["per_frame"]:
        c = pf["counts"]
        print(
            f"  step {pf['step']:>3}: "
            f"truth={c[TRUTH_CREATURE]:>2} lie={c[LIE_CREATURE]:>2} mixed={c[MIXED]:>2} "
            f"| n={pf['n_structures']:>3} cover={pf['total_coverage']:>4}"
        )


if __name__ == "__main__":
    main()
