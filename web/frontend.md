# Veridia v0.2 — 前端文档

> 本文描述 `web/` 下的前端：技术栈、怎么跑、组件地图、渲染管线、回放/实时两种模式，以及视觉皮肤规格与落地计划。
> 不变量（来自 `../veridia-v0.2-黑客松-72h作战图.md:10`）：**一切可视化 = 帧状态（Frame）的纯函数**。前端只经"帧状态契约"与后端耦合，详见 `../frontend-backend-契约.md`。

---

## 1. 技术栈与目录结构

| 维度 | 选型 | 出处 |
|---|---|---|
| 构建 | Vite 8 + `@vitejs/plugin-react` | `web/package.json:33`、`web/vite.config.ts` |
| 框架 | React 19 + ReactDOM 19 | `web/package.json:14` |
| 语言 | TypeScript ~6.0 | `web/package.json:31` |
| 渲染 | Canvas 2D（`putImageData`） | `web/src/ca/CanvasField.tsx:65` |
| 单测 | Vitest 4 + jsdom + Testing Library | `web/vitest.config.ts`、`web/package.json:34` |
| Lint | ESLint 10 + typescript-eslint | `web/package.json:25` |
| E2E | Playwright 1.61（**已装为 devDep，尚无 spec / 无 npm script**） | `web/package.json:30` |

目录（实际文件，`web/src/` 下）：

```
web/src/
  main.tsx                      # React 入口
  App.tsx                       # 顶层壳：晶族/雾族对局视图 + <CAView/>
  App.css / index.css           # 全局样式（注意：当前是 Vite 模板默认皮肤，紫色 accent）
  types.ts                      # 对局博弈 trace 的 TS 类型（Round/Trace，非 CA 帧契约）
  test-setup.ts                 # 引入 jest-dom 断言
  fixtures/sample-trace.json    # App 用的对局 trace 样例
  components/                   # 对局视图组件（与 CA 渲染无关）
    Scoreboard.tsx / Timeline.tsx / TrustChart.tsx (+ *.test.tsx)
  ca/                           # ★ CA 可视化主轴（本文重点）
    types.ts                    # 帧状态契约的 TS 镜像（Frame / MicroscopeRecord / CATrace）
    CAView.tsx                  # CA 视图壳：回放/实时模式切换 + 控件 + 点击判读
    CanvasField.tsx             # Frame → ImageData → <canvas> 的纯渲染器
    MicroscopePanel.tsx         # 显微镜侧板：展示 claim/verdict/reason
    liveEngine.ts               # 浏览器端实时 CA 引擎（移植 ca/rule.py + ca/engine.py）
    lenia.ts                    # Lenia 连续 CA 的 TS-CPU 移植（移植 ca/lenia.py）
    CAView.test.tsx / lenia.test.ts / liveEngine.test.ts
    fixtures/run-trace.json     # 后端 `python -m ca.run` 产物（真引擎帧 + 显微镜记录）
    fixtures/stub-trace.json    # 占位帧（旧）
```

> 提示：`web/src/types.ts`（顶层）描述的是 App 的"晶族 vs 雾族"对局 trace，与 CA 帧契约**是两套类型**。CA 的契约类型在 `web/src/ca/types.ts`。

---

## 2. 怎么跑（命令均来自 `web/package.json:6`，未编造）

```bash
cd web
npm install        # 安装依赖

npm run dev        # 开发服务器（vite）
npm run build      # 类型检查 + 产物构建（tsc -b && vite build）
npm run preview    # 预览 build 产物
npm run lint       # ESLint（eslint .）
npm run test       # 单元测试（vitest run）
```

E2E：`package.json` 里有 `playwright` 依赖但**没有** e2e/test:e2e 这类 script，也没有 spec 文件与 `playwright.config`。"视觉回归用 Playwright 截图对比"目前是**计划，未落地**（见 §7）。

---

## 3. 组件地图与数据流

核心数据流（CA 部分）：

```
后端 ca.run ──写──▶ web/src/ca/fixtures/run-trace.json
                              │ import
                              ▼
                        CAView (壳/状态机)
            ┌─────────────────┴─────────────────┐
        回放 ReplayView                     实时 LiveView
        读 trace.frames                  new LiveEngine(...).frame()
            │                                   │
            └──────────► frame: Frame ◄─────────┘
                              │ 纯函数
                              ▼
                        CanvasField(frame)
                  frameToImageData(frame) → putImageData
                              │
                  点击格子 →  MicroscopePanel(record)
```

- **`App.tsx`** (`web/src/App.tsx`)：顶层页面。先渲染"晶族 vs 雾族"对局视图（Scoreboard / TrustChart / Timeline，读 `fixtures/sample-trace.json`），底部挂 `<CAView/>`。CA 部分与对局部分相互独立。
- **`CAView.tsx`** (`web/src/ca/CAView.tsx:39`)：CA 视图壳，持有 `mode: "replay" | "live"`（`:40`），按钮切换两种子视图（`:60`）。
  - **`ReplayView`** (`:66`)：读 `run-trace.json` 的 `frames`，`step` 用 React state 驱动滑块/播放；`useEffect`+`setInterval(200ms)` 推进（`:76`）。点击 canvas → 像素坐标映射回格坐标 → `nearestRecord()`（`:17`，按 step 距离优先、再格距）在 `trace.microscope` 里找最近的一条判读记录。
  - **`LiveView`** (`:150`)：`engineRef` 持有 `LiveEngine` 实例（`useRef`，不进 React state）；`setInterval(120ms)` 调 `eng.step()` 后 `setFrame(eng.frame())` 触发重渲（`:160`）。点击 → `readCellOffline()` 用该格 `type/belief` 现算判读（`:185`，**不调 LLM**）。有播放/单步/重置三个控件。
- **`CanvasField.tsx`** (`web/src/ca/CanvasField.tsx:57`)：**纯渲染器**，入参只有 `frame: Frame`。`frameToImageData(frame)`（`:31`）把帧编成 `ImageData`，`useEffect` 里 `putImageData` 上屏（`:65`）。jsdom 下拿不到 2d 上下文时安全跳过绘制（`:64`），所以单测不崩。`<canvas>` 用 `imageRendering: "pixelated"`、`width/height` 设为帧网格尺寸，CSS 放大到 `maxWidth:480`（`:74`）。
- **`MicroscopePanel.tsx`** (`web/src/ca/MicroscopePanel.tsx:10`)：展示选中格的 `claim`（引述）、`verdict`（lie 红 / truthful 绿色 chip，`:33`）、`reason`。无选中时给提示文案。**只读、只在这一层落字，从不写回 CA。**
- **`liveEngine.ts`**、**`lenia.ts`**：浏览器端 CA 引擎与 Lenia 移植，详见 §4 与契约文档。

数据流要点（与作战图一致）：
- **渲染纯函数化**：`CanvasField` 只依赖 `frame`，无副作用、无内部状态；同一帧渲染结果确定。
- **rAF/useRef 而非 React state 存网格**：实时模式把可变网格放在 `LiveEngine`（`useRef`）里，React 只持有"当前要画的那一帧快照"和播放标志，避免大数组进 state 引发的重渲开销。
  - 现状说明：当前实时驱动用的是 `setInterval(120ms)`（`CAView.tsx:162`），**不是** `requestAnimationFrame`。设计目标是 rAF（见本文 §6 视觉皮肤规格）；这是已知差距，记于 §7。

---

## 4. 实时模式 vs 回放模式

| | 回放（replay，默认） | 实时（live） |
|---|---|---|
| 数据来源 | `fixtures/run-trace.json`（后端 `ca.run` 产物） | 浏览器内 `LiveEngine` 现算 |
| 帧 | 预生成、`stride=2` 抽样、3 位小数 | 每步现算、float32 全精度 |
| 显微镜 | `trace.microscope` 预计算记录（离线模板或 `--live` LLM） | `readCellOffline()` 确定性 TS 模板，**永不调 LLM** |
| 网格 | 48×48（见 `run.py:CONFIG`） | 64×64（`CAView.tsx:12` `LIVE_W/H`） |
| 切换 | `CAView` 顶部两个按钮 `ca-mode-replay` / `ca-mode-live`（`CAView.tsx:45`） | 同上 |

`LiveEngine`（`web/src/ca/liveEngine.ts:92`）是 `ca/engine.py` + `ca/rule.py` + `ca/lenia.py` 的忠实 TS 移植：每步 `Lenia(belief) → belief_update（诚实朝 F / 操纵者离 F） → standing_update（带符号可信度）`（`:188`），`.frame()` 导出契约 Frame（`:204`）。随机源用 `mulberry32`（`:50`）替代 numpy PCG64——**不保证逐格数值与 Python 一致**，只保证统计性质（噪声幅度 0.02、操纵者占比 ~25%、同 seed 可复现），见文件头注释 `:8`。

---

## 5. 渲染管线（现状 vs 设计目标）

### 5.1 现状（已落地，`CanvasField.tsx`）
单 canvas，逐格上色，无离屏、无辉光、无加色混合：
1. `frameToImageData(frame)`（`:31`）遍历每格：
   - `colormap(belief)`（`:19`）：冷端 `[20,40,90]` → 暖端 `[255,190,70]` **线性插值**（belief 0=谎冷暗，1=真暖亮）。
   - `standing` 调亮度，下限 0.35 保证可见（`:37`）。
   - `type` 轻微染色：操纵者偏品红，诚实偏青绿（`:42`）。
2. `putImageData` 一次写入（`:65`），CSS `imageRendering: pixelated` 整数放大到 480px（`:77`）。

> 与"复杂科学要看涌现结构"一致：**逐格上色、不做平均/扩散/插值**（`CanvasField.tsx:6`）。

### 5.2 设计目标（见本文 §6，**尚未实现**）
原 `docs/design.md`（已删除）规定的离散台阶辉光管线，目前代码里没有，列为待办（§7）：
- **双离屏架构**：`glowCanvas`（低分辨率画阶梯辉光 → 整数倍放大成像素化 bloom）+ `cellCanvas`（主分辨率硬边方块本体）+ `mainCanvas`（先 `drawImage(glow, 'lighter')` 再画 cells）。
- **离散阶梯辉光**：高 belief 细胞按格距向外画 2–4 圈渐暗暖色方块，圈圈硬边不插值（复刻 Minecraft 每格 −1 光级），belief 量化成 0–N 光级；操纵格用冷端色阶。
- **加色混合**：辉光层 `globalCompositeOperation='lighter'`，相邻发光重叠过曝变白；全屏薄铺暖膜 `#F4A65E` α0.06–0.12。
- **体素细胞**：方块 + 左上固定打光（顶/左 +1px 高光，底/右 +1px 暗边），硬边零抗锯齿无圆角。
- **全程** `imageSmoothingEnabled=false`、整数像素对齐；渲染走 `useRef`+`rAF`，**不进 React state**。
- MVP 兜底：先 `shadowBlur` 糊近似，正式版换离散台阶。

---

## 6. 视觉皮肤规格（来自已删除的 design.md，仍有效部分收录于此）

> 这些是前端视觉皮肤层的设计依据，**只规定怎么渲染/排版/呈现**，不动 CA 引擎、Frame 契约、自然神论与 litmus。
> 定调：在《光遇》式黄昏梦幻大气里，一格格 belief 细胞是"会发光的体素方块"；辉光按《我的世界》离散光级一层层叠出，而非高斯柔糊。
> **落地现状：以下绝大多数尚未实现**（当前 `index.css` 仍是 Vite 紫色模板皮肤，无 Cinzel/Cardo/Monocraft 字体，无 `theme.ts`）。

### 6.1 背景序章（锁定，全英文，Genesis/KJV 语调）
VERIDIA — An Emergent World of Truth and Lies。讲创世立法 F、神缺席、honest vs deceivers、"You are the Microscope"、"can truth endure on its own, with no god left to save it?"

### 6.2 字体（设计目标，未引入）
- Display/标题 = Cinzel（Trajan 罗马铭文大写复刻），`@fontsource/cinzel`
- Body/lore = Cardo（圣经/古典排版），`@fontsource/cardo`，EB Garamond 备选
- Data/读数 = Monocraft（MC 风等宽，`@font-face`），显微镜面板用
- 可选：标题首字母 drop-cap 用 UnifrakturMaguntia + 发光

### 6.3 配色板（hex tokens）
- 大气底渐变：`#0E1024`（顶）→ `#171A38` → `#2E3A6E` → `#5B5FA8`（下），地平线叠 `#F6C66B` 径向光晕
- Belief 暖端（信真）：核 `#FFE3A8` / 烛光金 `#F6C66B` / 暮色橙 `#F4A65E` / 玫瑰粉外缘 `#F4B7C2` / 暖金暗边 `#C98A3A`
- Belief 冷端（信谎/操纵）：谎言冷暗 `#3A4668` / 操纵冷蓝 `#2A6F97` / 暗边 `#1E5F8C` / 激活青 `#5DECF5` / 死寂近黑 `#0B2A3A`
- UI：雾白文字 `#E9E4F0` / 暖金激活 `#F6C66B` / 静默灰紫 `#8A8FB0`
- 语义：暖↔冷 = "有光 vs 被夺走光 vs 被注入人造冷蓝"，操纵 = 注入的突兀冷蓝

> 注意：当前 `CanvasField.colormap()` 用的是 `[20,40,90]→[255,190,70]` 线性插值，与上面 token 板**不同**——token 板属于未落地的视觉重做目标。

### 6.4 排版（canvas 当英雄主角）
顶栏极简（VERIDIA + 世代/存活率呼吸细环）；canvas 占 60%+；点细胞滑出显微镜侧板（默认收起/半透明，Monocraft 读数）；发光地平线带；底部控制条默认低透明 hover 升亮（▷播放 ⏸ ⏭步进 速度滑块 〔观察〕〔操纵〕）；序章放入口/侧栏。

### 6.5 交互状态（根治"假按钮"）
- 铁律（光遇）：一切反馈翻译成"光的明灭"，不用描边方框。
- idle=雾白低存在 / hover=升亮+辉光增大（`text-shadow 0 0 12px #F6C66B`）+缩放1.05 200-300ms / active=过曝到核 `#FFE3A8`+缩0.97回弹 / 选中=柔光环多层 box-shadow+呼吸 / playing=持续发光+缓脉动 / disabled=灰紫 `#8A8FB0` 辉光归零 / loading=角落呼吸细环加速不要 spinner。
- "假按钮"根因 = 裸 HTML 控件零反馈（不是逻辑坏），全部重做成发光元素即解。
- 避开：裸 Bootstrap/Material 控件、硬边框表状态、纯高斯糊当唯一 bloom、细胞圆角/抗锯齿、中性白底/纯黑底/荧光原色、满屏堆叠、快动效 spinner。

> 现状：`CAView` / `MicroscopePanel` 的控件仍是裸 `<button>` / `<input type=range>` 行内样式（如 `CAView.tsx:45`、`MicroscopePanel.tsx:33`），即上文所说的"假按钮"待重做态。

---

## 7. 前端待办 / 代码落地计划（对照真实代码标注完成度）

> 原 design.md §7 的计划（已退役，并入本文）。只动 `web/` 渲染+UI 层；**不改** Frame 契约 / CA 引擎 / 后端 / trace。

| # | 计划 | 现状 |
|---|---|---|
| 1 | 主题 tokens：`web/src/ca/theme.ts`（配色+字号+缓动）+ 全局 CSS 变量 | ❌ 未做。无 `theme.ts`；`index.css` 仍是 Vite 模板（紫 accent） |
| 2 | 字体：`@fontsource/cinzel`、`@fontsource/cardo`、Monocraft `@font-face`，`index.css` 应用 | ❌ 未做。`package.json` 无 fontsource 依赖，代码无字体引用 |
| 3 | 辉光渲染：重写 `CanvasField.tsx` → 双离屏 + 离散台阶 bloom（§5.2），入参仍是 Frame | ❌ 未做。当前为单 canvas 线性 colormap（契约入参已是 Frame，符合不变量） |
| 4 | 微显微镜：`MicroscopePanel.tsx` 改光遇侧板观感（Monocraft 读数、暖/冷判读色块、柔滑出） | ⚠️ 部分。已有 verdict 暖/冷色块（红/绿 chip），但非光遇皮肤、无 Monocraft、无滑出动效 |
| 5 | 壳与排版：`CAView.tsx` / `App.tsx` 重排成 §6.4 布局 + 发光按钮组件（§6.5） | ❌ 未做。当前裸控件 + 行内样式 |
| 6 | 显微镜光标 → 图标：cursor 换显微镜 SVG | ❌ 未做。当前 `cursor: "crosshair"`（`CAView.tsx:112`、`:202`） |
| 7 | 实时判读英文化：`liveEngine.ts` 的 `readCellOffline` 文案改全英文 | ❌ 未做。`readCellOffline` 文案仍为中文（`liveEngine.ts:246`） |
| 8 | 视觉回归：Playwright 截关键态对比 | ❌ 未做。playwright 已装为依赖，但无 spec / 无 config / 无 script |

**已落地且符合不变量的部分**：
- ✅ Frame 契约的 TS 镜像（`web/src/ca/types.ts`）。
- ✅ `CanvasField` 是 Frame 的纯函数渲染器（契约入参不变，皮肤可替换）。
- ✅ 回放/实时双模式 + 模式切换（`CAView.tsx`），实时引擎移植（`liveEngine.ts` / `lenia.ts`）。
- ✅ litmus：渲染层与实时引擎全程不 import 任何 LLM；关掉 LLM CA 照跑（见契约文档 §4）。
- ✅ 单测覆盖（`CAView.test.tsx`、`lenia.test.ts`、`liveEngine.test.ts` 等）。

### 核心 spike 对齐
视觉重做是纯皮肤层；核心 spike（复杂科学 CA / 自然神论 / litmus / 句法语义分层 / trace 驱动 / 帧状态契约）一寸未动，全部活在 `web/` 渲染+UI 层。
</content>
</invoke>
