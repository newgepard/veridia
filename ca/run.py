"""集成入口 —— 把 F1 引擎 + F2 显微镜拼成一条真 trace,喂前端。

默认(离线、零 LLM、无需 API key):
  python -m ca.run
  → 跑 CAEngine ~80 步,收成 ca.state.empty_trace 的 trace,
    用确定性 template_record 填 microscope,写 web/src/ca/fixtures/run-trace.json。

--live(真 LLM,本阶段只搭线不跑):
  python -m ca.run --live
  → 同样的帧,但 microscope 用 judge_cell + deepseek 真判读。
    需要 DEEPSEEK_API_KEY;离线提交的产物不走这条。

不变量:本入口的 CA 推进(engine.step 循环)不碰 LLM;LLM 只在 --live 的
显微镜环节出现,read-only,绝不写回 belief/type/standing。
"""
from __future__ import annotations

import argparse
import json
import os

from ca.engine import CAEngine
from ca.state import empty_trace, MANIPULATIVE
from ca.microscope import (
    template_record,
    precompute_microscope,
    legislate_F,
    make_llm_judger,
)

# 产物落点(前端 fixture)。
OUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "web", "src", "ca", "fixtures", "run-trace.json"
)

# trace 配置:网格 <= 64x64,步数 ~80,隔帧抽样让 JSON 不爆。
CONFIG = {
    "width": 48,
    "height": 48,
    "steps": 80,
    "seed": 7,
    "stride": 2,          # 每 2 步留一帧,控 JSON 体积
    "round_dp": 3,        # belief/standing 保留 3 位小数
    "note": "real run: Lenia belief field + signed-standing rule",
}


def _round_frame(d: dict, dp: int) -> dict:
    """把一帧 dict 里的 belief/standing 四舍五入到 dp 位,缩小 JSON。"""
    d["belief"] = [round(v, dp) for v in d["belief"]]
    d["standing"] = [round(v, dp) for v in d["standing"]]
    return d


def build_trace(config: dict) -> dict:
    """跑引擎收帧。确定性,无 LLM。"""
    width = config["width"]
    height = config["height"]
    steps = config["steps"]
    seed = config.get("seed", 0)
    stride = config.get("stride", 1)
    dp = config.get("round_dp", 3)

    engine = CAEngine(width, height, seed=seed)
    trace = empty_trace(game_id=f"veridia-ca-{seed}", config=config)

    # 收第 0 帧(初态),然后每 stride 步收一帧。
    trace["frames"].append(_round_frame(engine.frame().to_dict(), dp))
    for s in range(1, steps + 1):
        engine.step()
        if s % stride == 0:
            trace["frames"].append(_round_frame(engine.frame().to_dict(), dp))
    return trace


def pick_samples(trace: dict, per_frame: int = 3) -> list[tuple[int, int, int]]:
    """跨帧确定性地挑一批"有意思"的 cell 放大。

    策略:对若干个均匀分布的帧索引,各挑 per_frame 个 cell——优先挑既有
    manipulative(会判 lie)又有 honest(判 truthful)的格子,让显微镜两类都出现。
    纯确定性,不调 LLM。
    """
    frames = trace.get("frames", [])
    if not frames:
        return []
    n = len(frames)
    # 取约 8 个帧索引,均匀铺开。
    frame_idxs = sorted({round(i * (n - 1) / 7) for i in range(8)}) if n > 1 else [0]

    samples: list[tuple[int, int, int]] = []
    for fi in frame_idxs:
        frame = frames[fi]
        w, h = frame["width"], frame["height"]
        types = frame["type"]
        # 找一个 manipulative 和两个 honest 的格子(确定性扫描)。
        manip_xy = None
        honest_xys: list[tuple[int, int]] = []
        for i, t in enumerate(types):
            x, y = i % w, i // w
            if t == MANIPULATIVE and manip_xy is None:
                manip_xy = (x, y)
            elif t != MANIPULATIVE and len(honest_xys) < per_frame:
                honest_xys.append((x, y))
            if manip_xy is not None and len(honest_xys) >= per_frame:
                break
        if manip_xy is not None:
            samples.append((fi, manip_xy[0], manip_xy[1]))
        for (x, y) in honest_xys[: max(0, per_frame - 1)]:
            samples.append((fi, x, y))
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the veridia-ca run trace.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="用真 LLM(deepseek)judge_cell 填 microscope,而非确定性模板。需要 DEEPSEEK_API_KEY。",
    )
    parser.add_argument("--out", default=OUT_PATH, help="输出 JSON 路径。")
    args = parser.parse_args()

    trace = build_trace(CONFIG)
    samples = pick_samples(trace)

    if args.live:
        # 真 LLM 路径:法庭立法 F,再把 judge_cell 包成 judger。LLM 只读,不写回 CA。
        from sim.llm.providers import make_client

        client = make_client("deepseek")
        model = "deepseek-chat"
        F_sem = legislate_F(client, model)
        judger = make_llm_judger(client, model, F_sem)
        trace["config"] = {**trace["config"], "microscope": "live:deepseek", "F": F_sem}
    else:
        # 离线默认:确定性模板,零 LLM,无需 API key。
        judger = template_record
        trace["config"] = {**trace["config"], "microscope": "template"}

    trace["microscope"] = precompute_microscope(trace, judger, samples)

    out = os.path.abspath(args.out)
    with open(out, "w") as f:
        json.dump(trace, f, ensure_ascii=False)

    size = os.path.getsize(out)
    n_frames = len(trace["frames"])
    n_micro = len(trace["microscope"])
    print(
        f"wrote {out}\n"
        f"  frames={n_frames} microscope={n_micro} "
        f"grid={CONFIG['width']}x{CONFIG['height']} size={size/1024:.0f}KB "
        f"mode={'live' if args.live else 'template'}"
    )


if __name__ == "__main__":
    main()
