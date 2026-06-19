"""占位帧生成器 —— 不是真 CA 规则(真规则由 24h 发现冲刺搜出)。

漂移的高斯"生物",让前端渲染器从第 0 天就有活的、像涌现结构的目标可画。
真规则到了,换掉它、渲染器一行不改(契约不变)。
"""
import math
from ca.state import Frame, HONEST, MANIPULATIVE, empty_trace

# 几只会动的 belief "生物":(x_frac, y_frac, 符号) 符号>0 偏真、<0 偏谎
_BLOBS = [(0.30, 0.30, 1.0), (0.70, 0.62, -1.0), (0.52, 0.80, 0.7)]


def stub_frames(width: int = 48, height: int = 48, steps: int = 24) -> list[Frame]:
    frames: list[Frame] = []
    for s in range(steps):
        t = s / max(1, steps)
        belief: list[float] = []
        typ: list[int] = []
        standing: list[float] = []
        for y in range(height):
            for x in range(width):
                fx, fy = x / width, y / height
                v = 0.5
                for (bx, by, sign) in _BLOBS:
                    cx = bx + 0.15 * math.sin(2 * math.pi * (t + sign * 0.1))
                    cy = by + 0.15 * math.cos(2 * math.pi * (t + sign * 0.1))
                    d2 = (fx - cx) ** 2 + (fy - cy) ** 2
                    v += sign * 0.5 * math.exp(-d2 / 0.01)
                v = max(0.0, min(1.0, v))
                belief.append(v)
                typ.append(HONEST if v >= 0.5 else MANIPULATIVE)
                standing.append(0.5)
        frames.append(Frame(s, width, height, belief, typ, standing))
    return frames


def stub_trace(width: int = 48, height: int = 48, steps: int = 24, ndigits: int = 3) -> dict:
    tr = empty_trace("veridia-ca-stub", {"width": width, "height": height,
                                         "steps": steps, "note": "PLACEHOLDER, not the real rule"})
    for f in stub_frames(width, height, steps):
        d = f.to_dict()
        d["belief"] = [round(b, ndigits) for b in d["belief"]]
        d["standing"] = [round(s, ndigits) for s in d["standing"]]
        tr["frames"].append(d)
    return tr
