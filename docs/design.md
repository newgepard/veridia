# Veridia — Design (frontend visual + layout)

> 本文是前端**视觉皮肤层**的设计依据。它**只规定怎么渲染/排版/呈现**,不动 CA 引擎、Frame 契约、自然神论与 litmus(见 §6 核心 spike 对齐检查)。
> 一句话定调:**在《光遇》式黄昏梦幻大气里,一格格 belief 细胞是「会发光的体素方块」;辉光按《我的世界》离散光级一层层叠出,而非高斯柔糊。** 创世立法、神缺席、机械涌现——画面安静、辽阔、冷静的暖,像在看一座没有神在场、却自己亮起来的玻璃神殿。

## 1. Background intro(锁定,全英文,Genesis/KJV 语调)

```
VERIDIA
An Emergent World of Truth and Lies

In the beginning the Architect spoke one truth into the silence — and then withdrew.
No hand reaches down to mend the world. The law was laid at creation, and what
the law makes, it makes alone.

Upon the lattice two natures contend: the honest, who utter only what they hold
to be true; and the deceivers, who speak the opposite of what they know.

From a single law, life. Cells gather into creatures that drift, collide, and
consume; truth and falsehood spread across the field like light and shadow.

You are the Microscope — the one eye that reads meaning. Touch any cell to hear
its claim, and to know whether it lies.

One question is older than the world: can truth endure on its own,
with no god left to save it?
```

## 2. Typography(锁定)

- **Display / 标题 = Cinzel**(Trajan 罗马铭文大写的开源复刻)= **刻在石碑上的诫命**,贴「立法者之神在创世立法真理 F」。免费 Google Font。
- **Body / lore = Cardo**(专为圣经/古典学排版做,经卷感、可读)。EB Garamond 为备选。免费。
- **Data / 读数 = Monocraft**(开源 Minecraft 风等宽,无 Mojang 资产)→ 显微镜面板的 belief/判读用它,带体素气质。
- 可选重锤:标题首字母 drop-cap 用 **UnifrakturMaguntia**(古登堡圣经黑体字)+ 发光,呼应光遇辉光。
- 接入:Vite 里 `@fontsource/cinzel`、`@fontsource/cardo`;Monocraft 走 `@font-face`。

## 3. 配色板(hex)

**大气底渐变**:`#0E1024`(顶,创世深空)→ `#171A38` → `#2E3A6E` → `#5B5FA8`(下),地平线叠 `#F6C66B` 径向光晕。
**Belief 暖端=信真/创世微光**:核 `#FFE3A8` / 主色烛光金 `#F6C66B`(灵魂色)/ 暮色橙 `#F4A65E` / 玫瑰粉外缘 `#F4B7C2` / 暖金暗边 `#C98A3A`。
**Belief 冷端=信谎/操纵**:谎言冷暗 `#3A4668` / **操纵冷蓝 `#2A6F97`** / 暗边 `#1E5F8C` / 激活青 `#5DECF5` / 死寂近黑 `#0B2A3A`。
**UI**:雾白文字 `#E9E4F0` / 暖金激活 `#F6C66B` / 静默灰紫 `#8A8FB0`。
语义:暖↔冷**不是红蓝廉价对立,而是「有光 vs 被夺走光 vs 被注入人造冷蓝」**(操纵=神不在场时你这只手注入的突兀冷蓝)。

## 4. Canvas 2D 辉光(技术心脏:离散光级,非高斯糊)

- **离散阶梯辉光**:高 belief 细胞以本格为中心,按格距向外画 2–4 圈渐暗暖色方块,**圈圈硬边不插值**(复刻 Minecraft Light 每格 −1 的阶梯);belief 量化成 0–N 光级。操纵格用冷端色阶。
- **加色混合**:辉光层 `globalCompositeOperation='lighter'` → 相邻发光细胞重叠过曝变白(光遇 bloom 魂);全屏薄铺暖膜 `#F4A65E` α0.06–0.12 统一 magic-hour。
- **双离屏架构**:`glowCanvas`(低分辨率,只画阶梯辉光→整数倍放大,天然像素化 bloom)+ `cellCanvas`(主分辨率,硬边方块本体)+ `mainCanvas`(可见,先 drawImage(glow,'lighter') 再 cells)。全程 `imageSmoothingEnabled=false`、整数像素对齐。渲染走 `useRef`+rAF,**不进 React state**。
- **体素细胞**:方块 + 左上固定打光(顶/左 +1px 高光,底/右 +1px 暗边),硬边零抗锯齿无圆角(Orbium「生物」的体素身份证)。软的是它周围的光。
- MVP 兜底:先 `shadowBlur` 糊近似,正式版换离散台阶(别长期用,会糊掉方块魂)。

## 5. 排版(canvas 当英雄主角)

```
┌────────────────────────────────────────────────┐
│ ✦ VERIDIA   真相 vs 谎言·元胞自动机   ◜世代 1428◞│ 顶栏极简,右上呼吸细环=世代/存活率
│                ┌────────────────┐                │
│                │    C A N V A S  │   ┌─────────┐ │ 点细胞才滑出的显微镜侧板
│                │  (Orbium 在暮色  │   │显微镜    │ │ (默认收起/半透明,Monocraft 读数)
│                │   里发光呼吸)   │   │belief.82│ │
│                └────────────────┘   └─────────┘ │
│   ◜发光地平线带 (#F6C66B), 网格浮其上◞          │
├────────────────────────────────────────────────┤
│ ▷播放 ⏸ ⏭步进  ─速度●──  〔观察〕〔操纵〕      │ 底部控制条默认低透明,hover 升亮
└────────────────────────────────────────────────┘
```
canvas 占视觉 60%+,四周暮色负空间=辽阔;面板贴边可收;信息密度让位氛围。背景介绍(§1)用 Cardo 排在一个「序章」入口/侧栏。

## 6. 交互状态(根治"假按钮")

**铁律(光遇):一切反馈翻译成「光的明灭」,不用描边方框。**
| 状态 | 表现 |
|---|---|
| idle | 雾白图标 + 极淡辉光,低存在感 |
| hover | 升亮 + 辉光半径增大(text-shadow 0 0 12px `#F6C66B`)+ 缩放 1.05,200–300ms |
| active/按下 | 过曝到核 `#FFE3A8` + 缩到 0.97 回弹(像点亮烛火)|
| 选中(模式)| 套柔光环 box-shadow 多层 `#F6C66B` + 持续呼吸 |
| **playing** | 播放键持续发光高亮 + 极缓脉动 |
| disabled | 静默灰紫 `#8A8FB0`,辉光归零 |
| loading(未来 live-LLM)| 角落呼吸细环加速,**不要 spinner** |

> ⚠️ 当前"假按钮"根因=裸 HTML 控件零反馈(不是逻辑坏)。全部重做成发光元素即解。

**避开**:裸 Bootstrap/Material/默认控件、硬边框表状态、纯高斯糊当唯一 bloom、细胞圆角/抗锯齿、中性白底/纯黑底/荧光原色、满屏堆叠、快动效 spinner。

## 7. 代码落地计划(只动 web/ 渲染+UI 层)

1. **主题 tokens**:`web/src/ca/theme.ts`(§3 配色 + 字号 + 缓动常数);全局 CSS 变量。
2. **字体**:装 `@fontsource/cinzel`、`@fontsource/cardo`;Monocraft `@font-face`;`index.css` 应用。
3. **辉光渲染**:重写 `CanvasField.tsx` → 双离屏 + 离散台阶 bloom(§4),保持入参仍是 `Frame`(契约不变)。
4. **微显微镜**:`MicroscopePanel.tsx` 改光遇侧板观感(Monocraft 读数、暖/冷判读色块、柔滑出)。
5. **壳与排版**:`CAView.tsx` / `App.tsx` 重排成 §5 布局(canvas 英雄、控制条贴底、序章入口放 §1 英文介绍),发光按钮组件(§6)。
6. **显微镜光标→图标**:把 `cursor:"crosshair"` 换成一枚小**显微镜 SVG 图标**光标(`cursor:url(...)`),无美感的十字叉去掉。
7. **实时判读英文化**:`liveEngine.ts` 的 `readCellOffline` 文案改**全英文**(当前是中文,违反全英文要求)。
8. **视觉回归**:用 playwright 截关键态对比。
> 每步原子提交。不改:Frame 契约 / CA 引擎 / 后端 / trace。

## 8. 核心 spike 对齐检查(你要的)

**redesign 是纯皮肤,核心 spike 一寸未动——逐条核对:**
| 核心 spike | 重做是否触碰 | 为什么不破 |
|---|---|---|
| 复杂科学 CA(Lenia 涌现,非扩散)| ❌ 不碰 | 引擎仍是 lenia/rule/engine,只换"怎么把 Frame 画成像素" |
| 自然神论(创世立法 F、神缺席、read-only)| ❌ 不碰 | 显微镜/microscope 逻辑不动,只改面板观感 |
| litmus(关 LLM,CA 能跑)| ❌ 不碰 | 渲染层从不 import LLM |
| 句法/语义分层 | ❌ 不碰 | 视觉只在"呈现"层,不进机械/语义 |
| trace 驱动(一切是 Frame 的纯函数)| ✅ 强化 | 新渲染器入参仍是 `Frame`,纯函数性保持 |
| 帧状态契约 | ❌ 不碰 | `types.ts` Frame 不变,前后端契约稳 |

**结论:视觉重做完全活在 web/ 的渲染+UI 层,引擎/契约/哲学/守卫全部不动。spike 对齐 ✓。**
