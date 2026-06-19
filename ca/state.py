"""帧状态契约(作战图 §1,第 0-2h 地基)。后端吐它、前端渲它,唯一耦合点。

通道式(并行数组)——为帧率与紧凑 trace。**规则无关**:发现冲刺搜到的 CA 规则
换的是转移函数,永远不换这个形状。所以前端可对 stub 帧从第 0 天并行开工。
"""
from __future__ import annotations
from dataclasses import dataclass, asdict

# type 通道的紧凑编码
HONEST = 0
MANIPULATIVE = 1


@dataclass
class Frame:
    step: int
    width: int
    height: int
    belief: list[float]    # H*W 行优先, ∈[0,1] 连续(Lenia 场)
    type: list[int]        # H*W, 0=honest 1=manipulative
    standing: list[float]  # H*W, ∈[0,1]

    def idx(self, x: int, y: int) -> int:
        return y * self.width + x

    def to_dict(self) -> dict:
        return asdict(self)


def empty_trace(game_id: str, config: dict) -> dict:
    """顶层 CA trace 骨架。frames 逐帧追加;microscope 记录 LLM 点击判读。"""
    return {
        "game_id": game_id,
        "codename": "veridia-ca",
        "config": config,
        "frames": [],        # list[Frame.to_dict()]
        "microscope": [],    # list[{step,x,y,claim,verdict,reason}]
    }
