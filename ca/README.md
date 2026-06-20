# `ca/` — 后端核心（v0.2 复杂科学 CA）

> Veridia v0.2 的引擎层：晶族（honest）/ 雾族（manipulative）细胞在连续场上机械涌现，
> LLM 只作宪法法院（立法 F + 显微镜判读），read-only，绝不写回 CA。

## 文件地图

| 文件 | 职责 |
|---|---|
| `state.py` | **帧状态契约**：`Cell { belief, type, standing }`、`Frame`、`empty_trace()`、`MANIPULATIVE`。前后端唯一耦合点，详见根目录 [`frontend-backend-契约.md`](../frontend-backend-契约.md)。 |
| `lenia.py` | Lenia 连续 CA（Orbium 环核 + 高斯生长 + 直接卷积），belief 连续场的涌现引擎。 |
| `rule.py` | 转移规则：honest/manip nudge + 带符号 standing 演化（8-邻域）。 |
| `engine.py` | `CAEngine`：组合 lenia + rule，逐帧推进；`frame()` 吐出契约帧。 |
| `microscope.py` | LLM 显微镜（语义层）：`legislate_F` 立法、`template_record` 离线确定性判读、`make_llm_judger`/`judge_cell` 真 LLM 判读、`precompute_microscope`。 |
| `stub.py` | stub 帧生成器（前端可对随机场/占位帧先开工）。 |
| `run.py` | 集成入口：跑引擎收 trace + 填显微镜，写 `web/src/ca/fixtures/run-trace.json`。`--live` 走真 LLM。 |

## 不变量（litmus）

引擎推进（`engine.step` 循环）**不碰 LLM**；LLM 只在 `--live` 的显微镜环节出现，read-only。
关掉 LLM，CA 必须能跑到底。

## 对 `llm/` 的依赖

仅 `run.py --live` 用 `llm.providers.make_client`（根目录共享 LLM 层）。其余全自包含。
