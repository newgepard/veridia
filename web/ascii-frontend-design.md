# Veridia 前端设计 Spec —— ASCII 终端宇宙

> 日期:2026-06-20 · 状态:设计定稿待实现(brainstorming 产出)
> 取代已退役的"光遇×我的世界"辉光皮肤方向。前端美学改为 **ascii-magic 风格的实时 ASCII 终端宇宙**。
> 概念框架沿用:**晶族(honest,水晶的晶)/ 雾族(manipulative,起雾的雾)**;自然神论(F 立法、神缺席、read-only);LLM 宪法法院(显微镜判读)。

---

## 0. 一句话

把 CA 的 belief 场每帧实时渲成**彩色 ASCII 字符网格**——远看是涌现的字符生物在格子上厮杀,暖色=晶族、冷色=雾族;点开任意一只,**LLM 宪法法院以终端流水把它判成真/谎**。整个交互 app = 一座会自己亮起来的 ASCII 终端神殿。

## 1. 锁定的决策(brainstorming 结论)

| # | 决策 | 选定 |
|---|---|---|
| Q1 | ASCII 落点 | **在线 app 实时渲染**(自写渲染器;ascii-magic 仅风格参考,不引入其库) |
| Q2 | 阵营编码 | **颜色区分**:同一密度 ramp,晶族暖调 / 雾族冷调 |
| Q3 | 架构 | **换渲染器、其余复用**:只换"画"这一层,Frame 契约/实时引擎/回放/后端全不动 |

## 2. 架构与集成(改动面)

**唯一改动 = 渲染 + UI 皮肤层,活在 `web/`。Frame 帧契约、CA 引擎、liveEngine、后端、trace 一寸不动(litmus 与句法/语义分层守住)。**

新增 / 改写:
- `web/src/ca/asciiRenderer.ts` —— **新增,纯函数** `frameToGlyphs(frame, theme) → Array<{char, color, alpha}>`(长度 = width×height)。可独立单测,不碰 DOM/LLM。
- `web/src/ca/CanvasField.tsx` —— **改写**:用 canvas `fillText` 逐格画字符(等宽字体),颜色/字符来自 `asciiRenderer`。**入参仍是 `Frame`**(契约不变,纯函数性保持)。渲染走 `useRef`+rAF,不进 React state。
- `web/src/ca/theme.ts` —— **新增**:字符 ramp、双色调色板、字号、CRT 参数、缓动等 tokens(+ 全局 CSS 变量)。
- `web/src/ca/MicroscopePanel.tsx` —— **改写**:重皮成"宪法法院终端流水"(见 §4)。
- `web/src/ca/CAView.tsx` / `web/src/App.tsx` —— **重皮**成全屏终端框外壳(box-drawing 边框、终端控件)。数据流、replay/live 切换、play/step、click-to-inspect 逻辑不动。
- `web/src/ca/crt.ts` —— **新增(可选)**:CRT 后处理(扫描线 / vignette / bloom / 可选色差),CSS filter 或 canvas overlay 实现。

**不动**:`liveEngine.ts`、`lenia.ts`、`types.ts`(Frame 镜像)、`ca/*.py`、`llm/*`、`run-trace.json` 的形状。

## 3. 视觉语言

- **belief ∈ [0,1] → 密度 ramp(10 级)**:`· .:-=+*#%@`(块字 `· ░▒▓█` 为备选)。这是"远看涌现的生物"的来源。
- **type → 调色板(阵营靠颜色)**:
  - 晶族(honest)暖端:`#FFE3A8 → #F6C66B → #C98A3A`
  - 雾族(manipulative)冷端:`#2A6F97 → #5DECF5 → #0B2A3A`
  - 每个字符的颜色 = 按该格 belief 在其阵营色阶上取值。
- **bloom**:高 belief 字符叠加色混合(`globalCompositeOperation='lighter'`)→ 生物"发亮",用字符实现原辉光意图。
- **standing → 字符 alpha**:高 standing=更实、低=更虚(subtle,不抢 belief 的主表达)。
- **CRT 后处理**:扫描线 + 轻 vignette + magic-hour 暖膜薄铺;可选色差。底色近黑深空 `#0E1024`。
- 字体:等宽(优先系统等宽 / 可选 Monocraft 体素气质),`imageSmoothingEnabled=false`、整数像素对齐。

**渲染态示意**(暖/冷在真实里靠颜色分,这里都用密度示意):
```
╔══ VERIDIA ═══════════════════ gen 0034 · alive 73% ══╗
║      ..:--:..        ..:-=+=-:.                       ║
║    .:=*####*=:.     :=*#%@@%#*=:.                     ║
║    :=*#%@@%#*=:    .:=*##  ##*=:.    ← 暖色=晶族生物   ║
║    .:=*####*=:.     ..:-=+=-:..                       ║
║              ░▒▓▓▒░                                   ║
║            ░▒▓████▓▒░       ← 冷色=雾族(操纵冷蓝)     ║
║              ░▒▓▓▒░                                   ║
╠══════════════════════════════════════════════════════╣
║ [▶ PLAY] [⏭ STEP]  speed ▓▓▓░░   ‹ REPLAY | LIVE ›    ║
╚══════════════════════════════════════════════════════╝
     ▌ click any cell — the court will read it
```

## 4. 微显微镜 = 宪法法院终端(魔法时刻的载体)

点细胞 → 弹出"法庭流水",**打字机逐字**效果。数据**直接来自已烤进 `run-trace.json` 的真 DeepSeek 判读 + `config.F`**(回放模式),实时模式用 `liveEngine.readCellOffline`(已英文化):

```
┌─ CONSTITUTIONAL COURT · cell (12,7) @ step 34 ──────┐
│ F: The cell's environment is stable and predictable │
│ > CLAIM:  "I am fully aligned with the truth."      │
│ > NATURE: manipulative (雾族)   belief = 0.04       │
│ > VERDICT: ████ LIE ████                            │
│ > REASON: privately leans lie, asserts truth.       │
└─────────────────────────────────────────────────────┘
```
- `VERDICT`:`TRUTHFUL`=暖绿块 / `LIE`=冷红块。
- 全英文(判读语言已统一,见 `frontend-backend-契约.md` 风险点 #1 已闭合)。
- 取数走现有 `nearestRecord(trace.microscope, step, x, y)` 逻辑(`CAView.tsx`),不改契约。

## 5. 布局与交互

- 全屏终端框(box-drawing 边框);CA 当英雄主区,顶栏 `gen / alive%`,底栏控件。
- 控件做成 `[▶ PLAY]` `[⏭ STEP]` 文本按钮 + speed 文本滑条——**终端风天然根治"假按钮"**(原裸 HTML 控件零反馈的问题自然消解)。
- 保留:replay/live 切换、play/step、speed、click-to-inspect;hover 高亮该字符(整数格命中)。
- 终端块光标 `▌`;细胞命中用现有 canvas 坐标→格子换算(`CAView.tsx` 的 click 逻辑)。

## 6. 测试 / 兜底 / 协作

- **单测**:`asciiRenderer` 纯函数(belief→char 边界、type→palette 取色、空场、alpha 映射)。
- **视觉回归**:playwright 截早/中/晚帧 + 微镜态(playwright 已装,补 spec/script)。
- **兜底**:录屏(断网也能放);ASCII 录屏天然小而清晰,同时可喂视频组。
- **litmus 守护**:渲染层与 liveEngine 全程不 import LLM(沿用现有守卫)。

## 7. 不做(YAGNI)

- ❌ 全终端 TUI 重写(命令行交互)——只重皮,不改交互模型。
- ❌ ascii-magic 后处理着色器(双重渲染浪费)——自写渲染器。
- ⚠️ 开机逐字打 KJV 序章 = **可选锦上添花**,MVP 可砍;若做,放 `App` 入口、Enter 进世界。
- ❌ standing 显式数值面板(先只调 alpha;跑出来发现需要再加)。

## 8. 风险 / 待确认

- ⚠️ **协作红线**:前端同事正在跑 `web/`,这是前端美学大改。需与 ta 划清"谁做 `asciiRenderer`+`CanvasField` / 谁做 `CAView` 外壳+`MicroscopePanel`",否则撞车。**本 spec 作两人共同依据。**
- 性能:48²/64² 网格逐格 `fillText` @ rAF,中等格子应顺滑;若掉帧,降帧率或离屏缓存字形图集。
- ramp 字符集 / 块字二选一,最终以真实渲染观感为准(可在实现期 A/B)。
