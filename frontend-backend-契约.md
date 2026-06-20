# Veridia v0.2 — 前后端契约（集成面）

> 唯一耦合点是**帧状态契约（Frame）**。后端吐它、前端渲它（`ca/state.py:1`）。
> 不变量（作战图 `veridia-v0.2-黑客松-72h作战图.md`）：
> - "一切可视化 = 帧状态的纯函数；前后端只经帧状态契约耦合"（`:10`）。
> - "规则换的是转移函数，不换渲染器画的东西"（`:19`）。
> - **litmus**：关掉 LLM，CA 必须能跑到底（`:8`）。
> - 句法/语义分层：CA=句法（机械涌现）；LLM=语义（立法 F + 显微镜判读），是宪法/上诉法院，不进 CA 循环（`:11`）。

---

## 1. 帧状态契约（Cell / Frame）

作战图原文（`veridia-v0.2-黑客松-72h作战图.md:15`）：
```
Cell { belief: float∈[0,1](连续,Lenia 场), type: honest|manipulative, standing: float∈[0,1] }
```
实现采用**通道式（并行数组）**而非每格对象，为帧率与紧凑 trace（`ca/state.py:3`）。

### 1.1 字段逐项对照（Python ↔ TS）

| 字段 | Python (`ca/state.py:14`) | TS (`web/src/ca/types.ts:6`) | 一致？ |
|---|---|---|---|
| `step` | `int` | `number` | ✅ |
| `width` | `int` | `number` | ✅ |
| `height` | `int` | `number` | ✅ |
| `belief` | `list[float]` H*W 行优先, ∈[0,1] | `number[]` H*W 行优先, [0,1] | ✅ |
| `type` | `list[int]` H*W, 0=honest 1=manipulative | `number[]` H*W, 0=honest 1=manipulative | ✅ |
| `standing` | `list[float]` H*W, ∈[0,1] | `number[]` H*W, [0,1] | ✅ |

**枚举常量**：`HONEST=0`、`MANIPULATIVE=1`，两边一致（Python `ca/state.py:10`；TS `web/src/ca/types.ts:3`）。
**索引约定**：行优先 `i = y*width + x`，两边一致（Python `ca/state.py:23` `idx()`；TS `liveEngine.ts:216` `beliefAt`）。

> ✅ **结论：Frame 契约 Python ↔ TS 逐字段一致，无字段缺失/类型错位。** 这是集成的稳固地基。

> ⚠️ 命名注记：`type` 通道值域名 Python 注释写 "manipulative"，TS 写 "manipulative"；作战图原文写 `honest|manipulative`。三处语义一致，仅自然语言拼写偶有 "manipulator/manipulative" 混用（如 `liveEngine.ts:104` 注释），不影响数值契约。

### 1.2 `MicroscopeRecord`（显微镜判读记录）

| 字段 | Python（`microscope.template_record` 返回，`ca/microscope.py:137`） | TS (`web/src/ca/types.ts:15`) | 一致？ |
|---|---|---|---|
| `step` | int | number | ✅ |
| `x` | int | number | ✅ |
| `y` | int | number | ✅ |
| `claim` | str | string | ✅ |
| `verdict` | "truthful" \| "lie" | string `// "truthful" \| "lie"` | ✅（形状一致；TS 用裸 string，靠注释约束） |
| `reason` | str | string | ✅ |

形状一致。但**记录内容**两条产出路径不同，见 §5.2。

### 1.3 `CATrace`（顶层 trace）

| 字段 | Python（`empty_trace`，`ca/state.py:30`） | TS (`web/src/ca/types.ts:24`) | 一致？ |
|---|---|---|---|
| `game_id` | str | string | ✅ |
| `codename` | `"veridia-ca"` | string `// "veridia-ca"` | ✅ |
| `config` | dict | `Record<string, unknown>` | ✅ |
| `frames` | `list[Frame.to_dict()]` | `Frame[]` | ✅ |
| `microscope` | `list[record]` | `MicroscopeRecord[]` | ✅ |

✅ 顶层 trace 形状一致。前端 `CAView` 以 `rawTrace as unknown as CATrace` 直接消费（`CAView.tsx:9`）。

---

## 2. trace schema（逐帧 grid 快照 + 配置 + 显微镜记录）

CA trace 由 `python -m ca.run` 生成，写到 `web/src/ca/fixtures/run-trace.json`（`ca/run.py:32`）。结构：

```jsonc
{
  "game_id": "veridia-ca-7",
  "codename": "veridia-ca",
  "config": {                       // ca/run.py:CONFIG（:37）
    "width": 48, "height": 48, "steps": 80, "seed": 7,
    "stride": 2,                    // 每 2 步留一帧，控 JSON 体积
    "round_dp": 3,                  // belief/standing 保留 3 位小数
    "note": "...",
    "microscope": "template"        // 或 "live:deepseek"（--live 时），并附 "F"
  },
  "frames": [ { step, width, height, belief[], type[], standing[] }, ... ],
  "microscope": [ { step, x, y, claim, verdict, reason }, ... ]
}
```

- 帧抽样：收第 0 帧（初态）+ 之后每 `stride` 步收一帧（`ca/run.py:67`）。
- 体积控制：`belief`/`standing` 四舍五入到 `round_dp` 位（`ca/run.py:48`）。
- 显微镜样本：`pick_samples()` 跨约 8 个均匀帧、各挑 1 操纵者 + 若干诚实格，保证两类判读都出现（`ca/run.py:76`）。

> 注意区分**两套 trace**：
> - **CA trace**（本文）：`sim` 的 `TraceWriter`（`sim/trace.py:4`）**不生成**它；CA trace 由 `ca/state.empty_trace` 骨架 + `ca/run.py` 填充。
> - **对局博弈 trace**：`sim/trace.py:4` 的 `TraceWriter` 产出 `{game_id, codename:"veridia", config, rounds[], winner, metrics}`，对应前端 `web/src/types.ts:24` 的 `Trace` 与 `App.tsx`。
> 两者 `codename` 不同（`"veridia-ca"` vs `"veridia"`），schema 不同，互不混用。本契约文档只覆盖 **CA trace**。

---

## 3. 前后端如何耦合

- 前端**只**经 Frame 契约消费数据：`CanvasField` 入参就是 `Frame`（`CanvasField.tsx:57`），是 Frame 的纯函数。
- "规则换的是转移函数，不换渲染器画的东西"（作战图 `:19`）：后端 `ca/rule.py` / `ca/lenia.py` / `ca/engine.py` 怎么演化 belief/type/standing 都行，只要 `.frame()` 仍吐契约 Frame（`ca/engine.py:62`），前端**一行不用改**。
- 占位 → 真规则的平滑替换：早期前端对 `stub.py`（`ca/stub.py`，漂移高斯占位）开工，后端搜到真 Lenia 规则后换成 `run-trace.json`，"形状一致"（`CAView.tsx:7` 注释），渲染器零改动。

---

## 4. litmus 边界（前后端集成的验收红线）

**关掉 LLM，CA 必须能跑到底**（作战图 `:8`）。集成时这是硬红线，落实点：

- 后端 CA 引擎链不 import 任何 LLM：`ca/engine.py:6` 明确 "本文件及 ca.lenia / ca.rule 全程不 import 任何 LLM"。`ca/run.py` 默认离线、零 LLM、无需 API key（`ca/run.py:3`）。
- LLM 只在显微镜出现、read-only、绝不写回 CA：`ca/microscope.py:4`；`ca/run.py:13`。`--live` 仅替换 microscope 的产出方式，**不碰 engine.step 循环**（`ca/run.py:126`）。
- 前端渲染层从不 import LLM：`CanvasField.tsx`、`MicroscopePanel.tsx` 无任何 LLM 调用。实时引擎 `liveEngine.ts:6` "无 LLM、确定性 given seed"；实时点击判读 `readCellOffline()` 是确定性 TS 模板，明确"不调 LLM"（`liveEngine.ts:227`、`CAView.tsx:185`）。
- **验收红线**：任何"LLM 写回 belief/type/standing"（作战图称 Role D 越界）= 违规，MVP 禁止（`veridia-v0.2-黑客松-72h作战图.md:8`）。集成评审必须确认这条不被破坏。

---

## 5. 实时模式的数据接口

### 5.1 实时引擎怎么拿帧

`LiveEngine`（`web/src/ca/liveEngine.ts:92`）在浏览器内现算，**不经后端、不读 trace**：
- `new LiveEngine(W, H, seed)` 初始化（`CAView.tsx:153`，默认 64×64 / seed 0）。
- `engine.step()` 推进一帧：`Lenia(belief) → belief_update → standing_update`（`liveEngine.ts:188`），与 `ca/engine.py:51` 同序。
- `engine.frame()` 导出契约 Frame（`liveEngine.ts:204`），交给 `CanvasField` 渲染（`CAView.tsx:203`）。
- 只读访问器 `beliefAt/typeAt/standingAt`（`liveEngine.ts:216`）供点击判读取值。

> 移植保真度（`liveEngine.ts:8`）：转移函数与 `rule.py`/`engine.py` 逐式一致；唯一无法逐位复刻的是随机源——Python 用 numpy PCG64，TS 用 `mulberry32`。因此实时引擎**不保证逐格数值与 Python 后端相同**，只保证统计性质（噪声幅度 0.02、操纵者 ~25%、同 seed 可复现）。集成时**不要**拿实时帧去逐格对比后端 run-trace 帧。

### 5.2 实时判读怎么算（不调 LLM）

点击格子 → `readCellOffline(type, belief, x, y, step)`（`liveEngine.ts:232`）：
- `manipulator` → `verdict="lie"`（无论 belief，因发射谎言极 ≈0 与 F=1 相悖）。
- `honest` → `verdict="truthful"`（如实发射自身 belief）。
- 返回与契约 `MicroscopeRecord` 同形（`step,x,y,claim,verdict,reason`）。

---

## 6. ⚠️ 集成风险点：三条产出路径的判读内容不一致

Frame 契约**字段层面完全一致**（§1.1），但生成 `MicroscopeRecord` 的**三条路径文案/方向阈值不同**。形状能对齐，渲染不会崩，但**语义内容不可互换**，集成时需知情：

| 路径 | 代码 | verdict 判定 | claim 文案 |
|---|---|---|---|
| A. 后端离线模板 | `ca/microscope.py:119` `template_record` | `type==MANIPULATIVE → "lie"`，否则 `"truthful"` | 英文，如 `"My belief in the truth proposition is 0.42"` |
| B. 后端 LLM 真判读 | `ca/microscope.py:87` `judge_cell` | **机械权威值**（由真诚度定，非取 LLM），`sincere → "truthful"` else `"lie"`（`:95`） | LLM 生成的英文话语 |
| C. 前端实时离线 | `liveEngine.ts:232` `readCellOffline` | 同 A：`MANIPULATIVE → "lie"` else `"truthful"` | **中文**，如 `"真相是零 —— 这里什么都不可信。"` |

**风险/不一致清单**：
1. **A/B 是英文、C 是中文。** 原 design.md §7-step7（已退役）要求把 `readCellOffline` 文案英文化，**尚未做**（见 `web/frontend.md` §7）。回放面板会显示英文，实时面板显示中文 —— 同一 UI 两种语言。
2. **方向阈值在 B 与 C 不同。** 后端 `derive_pole_facts`（`ca/microscope.py:58`）用 `belief>=0.5` 分"私下偏真/偏谎"；前端 `readCellOffline` 的 honest 文案用 `0.66 / 0.33` 三档分 stance（`liveEngine.ts:252`）。两者都不改 verdict（verdict 只看 type），但**叙述阈值不一致**，对账时别误判为 bug。
3. **A 与 B 的 claim 含义相反须警惕。** `template_record`（A）对 manipulator 直接造一句"假装对齐真相"的话（`ca/microscope.py:129`）；`judge_cell`（B）让 LLM 生成"断言其发射极"的话。两者都标 `verdict="lie"`，但话术不同。这是历史上"方向反转 bug"的高发区——后端已把方向在 Python 算死（`ca/microscope.py:51` 注释），verdict **不取 LLM**（`ca/microscope.py:111`），属已修复的防御。
4. **邻域口径不同（非契约字段，仅内部统计）**：`standing_update` 用 8-邻域（`ca/rule.py:65`、`liveEngine.ts:74`），而 `_cell_state_at` 的 `neighbor_summary` 用 4-邻域（`ca/microscope.py:158`）。前者参与 standing 演化（影响契约 standing 值，两边都 8-邻域，一致），后者只喂给 LLM 当上下文（不入契约）。不冲突，记录备查。
5. **数值精度差**：后端 run-trace 帧是 3 位小数（`ca/run.py:48`），实时引擎是 float32 全精度。叠加随机源差异（§5.1），实时帧与回放帧**不可逐格对账**。

> 以上 1–5 **均不破坏 Frame 字段契约**，前端渲染不会崩；它们是"集成时容易误判为故障、实为预期差异"的点，列出供防翻车。

---

## 7. 集成验收清单（接通时逐项勾）

接通前后端（用真 `run-trace.json` 替换 / 升级引擎规则）时，过以下 smoke test：

- [ ] **真帧能渲染不崩**：`python -m ca.run` 生成 `web/src/ca/fixtures/run-trace.json` 后，`npm run dev` 打开，回放模式 canvas 出图、拖滑块换帧无报错。（对应 `CAView.test.tsx:8` "renders the CA canvas"）
- [ ] **关 LLM 能跑到底**（litmus）：不带 `--live`（无 API key）下 `python -m ca.run` 必须成功产出完整 trace；`engine.step` 循环全程不调 LLM。
- [ ] **字段对齐**：trace 每帧含 `step/width/height/belief/type/standing`，`len(belief)==len(type)==len(standing)==width*height`，`belief/standing ∈ [0,1]`，`type ∈ {0,1}`。
- [ ] **行优先索引一致**：抽一格 `(x,y)`，后端 `frame.idx(x,y)` 与前端 `y*width+x` 取到同一元素。
- [ ] **显微镜记录形状齐全**：每条含 `step,x,y,claim,verdict,reason`，`verdict ∈ {"truthful","lie"}`。
- [ ] **点击判读联动**：回放点格 → `nearestRecord` 命中、面板显示对应 claim/verdict（`CAView.tsx:101`）；实时点格 → manipulator 出 "lie"、honest 出 "truthful"（`CAView.test.tsx:76`）。
- [ ] **模式切换不破 v0.1/v0.2**：replay ↔ live 来回切，回放滑块与显微镜提示仍在（`CAView.test.tsx:66`）。
- [ ] **渲染层无 LLM import**：`grep -ri "llm\|deepseek\|anthropic\|openai" web/src/ca/CanvasField.tsx web/src/ca/MicroscopePanel.tsx web/src/ca/liveEngine.ts web/src/ca/lenia.ts` 应为空。
- [ ] **前端单测绿**：`cd web && npm run test` 全过（含 `CAView`/`lenia`/`liveEngine` 套件）。
- [ ] **（已知差异，非阻塞）** 接受：实时帧 ≠ 回放帧逐格数值（随机源/精度差，§5.1、§6-5）；面板文案回放英文 / 实时中文（§6-1，待英文化）。
</content>
