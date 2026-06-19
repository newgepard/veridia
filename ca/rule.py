"""真/谎主题 —— 固定本地规则(无 LLM)。

在 Lenia 的 belief 场之上叠一层语义本地规则:
- type 场: 0=honest(诚实), 1=manipulator(操纵者),固定不变。
- F: 真相吸引子(truth attractor),默认 1.0。
- 诚实格把自身 belief 朝 F 微调;操纵者格把 belief 推离 F。
- standing 按 **LOCKED 带符号可信度规则**演化:
    s_new = clamp01(s + eta * mean_over_neighbors( b_h * (1 - 2*|c - b_h|) ))
  其中 c 是该格发射的 claim(诚实发射=belief;操纵者发射=谎言极 0),
  b_h 是邻居中诚实格的 belief。纯/本地/确定。

全部 numpy 向量化、环面边界、无任何 LLM import。
"""
from __future__ import annotations
from dataclasses import dataclass

import numpy as np

from ca.state import HONEST, MANIPULATIVE


@dataclass
class RuleParams:
    F: float = 1.0          # 真相吸引子
    honest_pull: float = 0.05   # 诚实格朝 F 的微调强度
    manip_push: float = 0.05    # 操纵者格推离 F 的强度
    eta: float = 0.1        # standing 学习率
    lie_pole: float = 0.0   # 操纵者发射的谎言极


def clamp01(a: np.ndarray) -> np.ndarray:
    return np.clip(a, 0.0, 1.0)


def emitted_claim(belief: np.ndarray, type_field: np.ndarray,
                  params: RuleParams) -> np.ndarray:
    """每格发射的 claim c:诚实=自身 belief,操纵者=谎言极。"""
    c = np.where(type_field == MANIPULATIVE, params.lie_pole, belief)
    return c.astype(np.float64)


def belief_update(belief: np.ndarray, type_field: np.ndarray,
                  params: RuleParams) -> np.ndarray:
    """语义本地规则对 belief 的微调:诚实朝 F,操纵者离 F。返回 clamp 后的场。"""
    b = np.asarray(belief, dtype=np.float64)
    honest_mask = type_field == HONEST
    manip_mask = type_field == MANIPULATIVE
    delta = np.zeros_like(b)
    # 诚实:朝 F 拉
    delta[honest_mask] = params.honest_pull * (params.F - b[honest_mask])
    # 操纵者:推离 F(沿 b-F 方向放大)
    delta[manip_mask] = params.manip_push * (b[manip_mask] - params.F)
    return clamp01(b + delta)


def _neighbor_mean(field: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """对每格,取其 8 邻域中 mask=True 的格上 field 的均值(环面)。

    无满足条件的邻居时该格取 0(无诚实邻居 → 无信号)。
    """
    masked_vals = np.where(mask, field, 0.0).astype(np.float64)
    count = mask.astype(np.float64)
    sum_acc = np.zeros_like(masked_vals)
    cnt_acc = np.zeros_like(count)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            sum_acc += np.roll(np.roll(masked_vals, dy, axis=0), dx, axis=1)
            cnt_acc += np.roll(np.roll(count, dy, axis=0), dx, axis=1)
    safe = np.where(cnt_acc > 0, cnt_acc, 1.0)
    out = sum_acc / safe
    out[cnt_acc == 0] = 0.0
    return out


def standing_update(standing: np.ndarray, belief: np.ndarray,
                    type_field: np.ndarray, params: RuleParams) -> np.ndarray:
    """LOCKED 带符号可信度规则。

    对每格,把其 claim c 拿去和"诚实邻居的 belief b_h"对账:
      贡献 = b_h * (1 - 2*|c - b_h|)
    取邻域均值乘 eta 累加到 standing,clamp 到 [0,1]。
    """
    s = np.asarray(standing, dtype=np.float64)
    b = np.asarray(belief, dtype=np.float64)
    c = emitted_claim(b, type_field, params)

    honest_mask = type_field == HONEST
    # 诚实邻居的 belief 均值 b_h(每格视角)
    b_h = _neighbor_mean(b, honest_mask)
    # 带符号可信度信号: b_h * (1 - 2*|c - b_h|)
    signal = b_h * (1.0 - 2.0 * np.abs(c - b_h))
    s_new = clamp01(s + params.eta * signal)
    return s_new
