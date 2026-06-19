"""CAEngine —— 复杂科学基底的驱动器(无 LLM,确定性)。

每步:Lenia 更新 belief 场(连续涌现) + rule.py 的语义本地规则更新
type/standing。.frame() 把当前态导成契约 Frame(ca.state.Frame)。

LITMUS:本文件及 ca.lenia / ca.rule 全程不 import 任何 LLM。
"""
from __future__ import annotations

import numpy as np

from ca.state import Frame, HONEST, MANIPULATIVE
from ca.lenia import LeniaParams, make_kernel, lenia_step, seed_orbium
from ca.rule import RuleParams, belief_update, standing_update


class CAEngine:
    """连续 CA 引擎。belief 走 Lenia,type/standing 走固定语义规则。

    确定性:给定 seed 输出完全可复现。
    """

    def __init__(self, width: int, height: int, seed: int = 0,
                 params: dict | None = None):
        self.width = int(width)
        self.height = int(height)
        self.seed = int(seed)
        self.step_count = 0
        self.rng = np.random.default_rng(self.seed)

        params = params or {}
        self.lenia = LeniaParams(**params.get("lenia", {}))
        self.rule = RuleParams(**params.get("rule", {}))
        self._kernel = make_kernel(self.lenia)

        # belief 场:放一只 Orbium("生物"),保证活的可滑行涌现结构
        self.belief = seed_orbium(self.width, self.height)
        # 加一点确定性噪声让场不至于全 0(也让多 seed 有差异),但不淹没 Orbium
        noise = self.rng.random((self.height, self.width)) * 0.02
        self.belief = np.clip(self.belief + noise, 0.0, 1.0)

        # type 场:确定性地按种子撒操纵者(约 25%),固定不变
        self.type = np.where(
            self.rng.random((self.height, self.width)) < 0.25,
            MANIPULATIVE, HONEST,
        ).astype(np.int64)

        # standing 场:从中性 0.5 起
        self.standing = np.full((self.height, self.width), 0.5, dtype=np.float64)

    def step(self) -> None:
        """推进一帧:Lenia(belief) → 语义规则(belief 微调 + standing)。"""
        # 1) 复杂科学层:Lenia 连续更新
        self.belief = lenia_step(self.belief, self.lenia, self._kernel)
        # 2) 语义本地规则:真/谎对 belief 的微调
        self.belief = belief_update(self.belief, self.type, self.rule)
        # 3) LOCKED 带符号可信度规则:standing 演化(用更新后的 belief)
        self.standing = standing_update(
            self.standing, self.belief, self.type, self.rule)
        self.step_count += 1

    def frame(self) -> Frame:
        """导出当前态为契约 Frame(行优先扁平化)。"""
        return Frame(
            step=self.step_count,
            width=self.width,
            height=self.height,
            belief=self.belief.reshape(-1).astype(float).tolist(),
            type=self.type.reshape(-1).astype(int).tolist(),
            standing=self.standing.reshape(-1).astype(float).tolist(),
        )
