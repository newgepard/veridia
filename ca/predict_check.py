"""可预测性快检(held-out prediction)—— A 方案的命门。

证明 LLM 对细胞的真/谎解读**有预测力**:它能据当前帧的真/谎判读,预测该 cell
的 belief 在未来 k 帧朝"真极(1)"还是"谎极(0)"移动,而不是事后看云朵讲故事。

不变量(承袭显微镜):
  - LLM 只读,只给它**截至当前帧**的信息,绝不泄露未来帧(holdout)。
  - 方向真值来自 trace 里真实的 belief[t+k]-belief[t] 符号(机械事实),不取 LLM。
  - LLMClient 可注入(签名接 llm,内部 llm.complete),FakeLLM 即可单测,无需 API key。

约定:晶族=honest(真诚,说自己那一极)、雾族=manipulative(起雾、撒谎,说相反那一极)。

sample 里的 step_index 是 **frames 列表索引**(与 microscope.precompute_microscope 一致),
"未来 k 帧"= frames 列表里往后数 k 个元素(因隔帧抽样,实际跨 k*stride 个 CA step)。
"""
from __future__ import annotations

import argparse
import json
import os

from ca.microscope import _cell_state_at, _extract_json, derive_pole_facts

# 预测法官:据当前帧的真/谎解读,预测该 cell 的 belief 未来朝哪极漂。
# 与 judge 同源:方向真值由 Python 算死,这里 LLM 是真在"预测"(它看不到未来帧)。
PREDICT_SYSTEM = (
    "You are a forecasting microscope over a cellular world. "
    "CONVENTION: each cell holds a belief in [0,1] about ONE truth proposition F; "
    "1.0 = the TRUTH pole of F, 0.0 = the LIE pole. "
    "You are given F, ONE cell's CURRENT state, and AUTHORITATIVE DERIVED FACTS about "
    "whether the cell is sincere and which pole it privately leans toward / asserts. "
    "Using ONLY the current state and your reading of its truthfulness, PREDICT which way "
    "the cell's belief will move over the next few steps: toward the TRUTH pole (1) or "
    "toward the LIE pole (0). You are NOT shown any future state — this is a genuine forecast. "
    'Respond with ONLY JSON: '
    '{"direction": "toward_truth" | "toward_lie", "reason": "<short>"}.'
)


def _build_predict_user(F_sem: dict, cell_state: dict, facts: dict) -> str:
    """构造预测提示——**只含截至当前帧的信息**,绝不含未来帧。"""
    return (
        f"TRUTH PROPOSITION F:\n{json.dumps(F_sem)}\n\n"
        f"CELL CURRENT STATE:\n{json.dumps(cell_state)}\n\n"
        "AUTHORITATIVE DERIVED FACTS (about the CURRENT frame only):\n"
        f"- privately leans toward the {facts['private_pole'].upper()} pole\n"
        f"- its utterance asserts the {facts['emitted_pole'].upper()} pole\n"
        f"- it is therefore {'SINCERE (truthful)' if facts['sincere'] else 'LYING (a lie)'}\n\n"
        "Predict where its belief will head next. Return JSON "
        '{"direction": "toward_truth" | "toward_lie", "reason": "<short>"}.'
    )


def predict_one(llm, model: str, F_sem: dict, cell_state: dict) -> dict:
    """对单个 cell 的当前状态,让 LLM 预测 belief 漂向。fail-closed。

    返回 {"direction": "toward_truth"|"toward_lie", "reason": ...}。
    解析失败 → fail-closed 到 "toward_truth"(中性默认,并标注 reason)。
    """
    facts = derive_pole_facts(cell_state)
    user = _build_predict_user(F_sem, cell_state, facts)
    raw = llm.complete(PREDICT_SYSTEM, user, model)
    try:
        data = _extract_json(raw)
    except (ValueError, KeyError, TypeError):
        return {"direction": "toward_truth", "reason": "unparseable prediction output"}
    direction = data.get("direction", "")
    if direction not in ("toward_truth", "toward_lie"):
        # 非法/缺失方向也 fail-closed:不让脏数据混进准确率统计的"有效预测"。
        return {"direction": "toward_truth", "reason": "invalid direction in prediction"}
    return {"direction": direction, "reason": data.get("reason", "")}


def _actual_direction(trace: dict, step_index: int, x: int, y: int, k: int):
    """真值:belief[frames[step_index+k]] - belief[frames[step_index]] 的符号。

    返回 "toward_truth"(变大)/"toward_lie"(变小)/None(无未来帧或恰好不变)。
    **只在这里碰未来帧**,且只用于对账,绝不流入给 LLM 的提示。
    """
    frames = trace.get("frames", [])
    fut = step_index + k
    if step_index < 0 or fut >= len(frames):
        return None
    cur = frames[step_index]
    nxt = frames[fut]
    i = y * cur["width"] + x  # frame 是 dict(行优先索引),与 state.Frame.idx 同
    delta = float(nxt["belief"][i]) - float(cur["belief"][i])
    if delta > 0:
        return "toward_truth"
    if delta < 0:
        return "toward_lie"
    return None  # 恰好不变:无方向真值,跳过(不计入准确率)。


def predict_check(trace: dict, llm, model: str, samples, k: int = 8) -> dict:
    """可预测性快检主函数。

    对每个被抽样的 cell (step_index, x, y):
      1) 取该帧 cell 状态 + F 语义,**只给 LLM 截至当前帧的信息**(不泄露未来帧);
      2) 让 LLM 据真/谎解读预测 belief 未来 k 帧朝真极还是谎极漂;
      3) 用 trace 真实 belief[t+k]-belief[t] 符号作 ground truth 对账;
      4) 返回 {accuracy, n, baseline, per_sample}。accuracy 显著 > 0.5 = 解读有预测力。

    无未来帧 / delta 恰为 0 的样本被跳过(不计入 n 与 accuracy)。
    F 语义优先取 trace.config.F,没有则给占位(不影响对账,只影响提示文本)。
    """
    F_sem = trace.get("config", {}).get("F") or {
        "proposition": "(unknown)", "truth_pole": "(unknown)", "lie_pole": "(unknown)",
    }
    frames = trace.get("frames", [])

    per_sample: list[dict] = []
    correct = 0
    n = 0
    for (step_index, x, y) in samples:
        if step_index < 0 or step_index >= len(frames):
            continue
        frame = frames[step_index]
        w, h = frame["width"], frame["height"]
        if not (0 <= x < w and 0 <= y < h):
            continue
        actual = _actual_direction(trace, step_index, x, y, k)
        if actual is None:
            continue  # 无未来帧或 belief 不变:无真值,跳过。
        cell_state = _cell_state_at(frame, x, y)
        pred = predict_one(llm, model, F_sem, cell_state)
        hit = pred["direction"] == actual
        n += 1
        if hit:
            correct += 1
        per_sample.append({
            "step_index": step_index,
            "step": frame["step"],
            "x": x,
            "y": y,
            "predicted": pred["direction"],
            "actual": actual,
            "correct": hit,
            "reason": pred["reason"],
        })

    accuracy = correct / n if n else 0.0
    return {
        "accuracy": accuracy,
        "n": n,
        "baseline": 0.5,
        "per_sample": per_sample,
    }


def _load_trace(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


DEFAULT_TRACE = os.path.join(
    os.path.dirname(__file__), "..", "web", "src", "ca", "fixtures", "run-trace.json"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="可预测性快检:LLM 真/谎解读能否预测结构下一步行为。"
    )
    parser.add_argument("--trace", default=DEFAULT_TRACE, help="run-trace.json 路径。")
    parser.add_argument("--provider", default="deepseek", help="LLM provider(默认 deepseek)。")
    parser.add_argument("--k", type=int, default=8, help="向前看多少帧作真值(默认 8)。")
    parser.add_argument(
        "--per-frame", type=int, default=3, help="每个抽样帧取几个 cell(默认 3)。"
    )
    args = parser.parse_args()

    trace = _load_trace(os.path.abspath(args.trace))

    # 复用 run.pick_samples 的确定性抽样策略,保证检的就是显微镜放大过的那批 cell。
    from ca.run import pick_samples
    from llm.providers import make_client

    samples = pick_samples(trace, per_frame=args.per_frame)
    client = make_client(args.provider)
    model = "deepseek-chat" if args.provider == "deepseek" else None

    result = predict_check(trace, client, model, samples, k=args.k)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(
        f"\naccuracy={result['accuracy']:.3f} over n={result['n']} "
        f"(baseline={result['baseline']}, k={args.k})"
    )


if __name__ == "__main__":
    main()
