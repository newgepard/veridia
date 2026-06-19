# Veridia — Codex 视觉生成 Prompt(自包含)

> **为什么单独有这份:** `design.md` 是给工程实现看的设计依据,里面含 §7 代码计划(绑死了我们仓库的 `CanvasField.tsx` / `CAView.tsx` 等具体文件)+ §8 spike 自检 + 大量中文实现叙述。直接把它喂 Codex 生图/生 mockup,模型会被这些工程噪声带跑(去改我们的代码,而不是「生几版给你挑」)。这份是从 `design.md`(锁定:《光遇》×《我的世界》)+ `视觉参考-审美研究报告.md` 综合出的**自包含**生成 brief——删掉工程噪声、补上生成模型需要的视觉语言。
>
> **怎么用:**
> - 想要**概念氛围图(文生图)** → 复制 **PART A** 整段喂模型,生 3–4 张挑方向。
> - 想要**能在浏览器点的 mockup(生 HTML / React 单页)** → 复制 **PART B** 整段喂 Codex。
> - 两个 PART 用的是同一套**光遇×我的世界**配色字体(与研究报告的 Orbitron 科幻天文台体系**不是一套**,别混)。

---

## PART A — Image prompt(英文,原样粘贴)

```
A dark dusk void, sacred and immense. Glowing voxel cellular creatures — Orbium-like
Lenia gliders built from hard-edged Minecraft blocks — drift and breathe across a faint
lattice. Each block self-illuminates in DISCRETE STEPPED light levels (like Minecraft
light propagation, NOT gaussian blur); where neighboring glows overlap they bloom
ADDITIVELY toward warm white, the radiant dreamy bloom of the game Sky (《光遇》).

Warm candle-gold cells = TRUTH (core #FFE3A8, soul-gold #F6C66B, dusk-orange #F4A65E,
rose-pink fringe #F4B7C2). Cold injected blue cells = LIES / MANIPULATION (#2A6F97,
activated cyan #5DECF5) — they read as light that was STOLEN or artificially injected,
not light that belongs.

Background: a vertical atmospheric sky gradient, deep creation-void #0E1024 at the top
through #171A38 and #2E3A6E to #5B5FA8 below, with a softly glowing horizon band #F6C66B
and a faint creation grid floating over it. Vast quiet negative space around the creature.

A carved Trajan / Cinzel stone-inscription title "VERIDIA" in Roman capitals, faintly
glowing. A single microscope-eye observing the field from above.

Mood: Genesis / King James Bible, DEIST — one law was spoken at creation and the god then
withdrew; life emerges from that single law, alone, with no hand reaching down to save it.
Magic-hour, high-contrast dark field, cinematic and painterly, solemn, sharp, not sweet.

NOT cartoon, NOT candy colors, NOT pure-black background, NOT neon-soaked, NOT rounded
glossy UI, NOT a bright lab/whiteboard look.
```

---

## PART B — Mockup spec(自包含,给 Codex 生代码)

**Goal:** Generate ONE self-contained file — either a single `index.html` (inline CSS + JS) or a single React + TypeScript component — that renders a **static hero mockup** of the Veridia screen. A fake glowing creature painted on a `<canvas>` plus the floating HUD is enough; **no real simulation is required**. **Do NOT assume any existing repo files, imports, or build setup** — everything must be inline and runnable on its own.

**Theme:** A floating temple of glass over a living dusk world — 《光遇》(Sky) dreamy radiance × 《我的世界》(Minecraft) hard voxel blocks. Sacred, Genesis-toned, a deist world the god has left. Calm, vast, a cold-warm.

**Palette (hex — use exactly):**
- Atmosphere sky (top→bottom): `#0E1024` → `#171A38` → `#2E3A6E` → `#5B5FA8`; glowing horizon radial `#F6C66B`.
- Belief warm = truth / creation-light: core `#FFE3A8`, soul candle-gold `#F6C66B`, dusk-orange `#F4A65E`, rose-pink fringe `#F4B7C2`, warm dark edge `#C98A3A`.
- Belief cold = lies / manipulation: lie cold-dark `#3A4668`, manipulation blue `#2A6F97`, dark edge `#1E5F8C`, activated cyan `#5DECF5`, dead near-black `#0B2A3A`.
- UI: misty-white text `#E9E4F0`, warm-gold active `#F6C66B`, muted grey-violet `#8A8FB0`.

**Typography:**
- Title / display = **Cinzel** (Trajan carved-stone Roman capitals — the engraved commandment). Google Fonts.
- Body / lore = **Cardo** (biblical / classical serif — set the Genesis intro below in it). Google Fonts.
- Data / readouts = a **pixel monospace** for the Minecraft-voxel feel (use `Silkscreen` or `Pixelify Sans` from Google Fonts, or `Monocraft`).

**Canvas glow technique (the visual heart):**
- Voxel cells = hard-edged squares, NO anti-aliasing, NO rounded corners; each square gets a 1px top-left highlight + 1px bottom-right dark edge (fixed light source) so it reads as a lit block.
- Glow = DISCRETE stepped rings of dimming warm color radiating from bright cells, hard edges, no interpolation (Minecraft light, −1 per cell-step) — NOT a gaussian blur.
- Composite the glow layer ADDITIVELY (`globalCompositeOperation = 'lighter'`) so overlapping glows overexpose to warm white (the Sky bloom). `imageSmoothingEnabled = false`, integer-pixel aligned.
- Thin warm film over everything: fill `#F4A65E` at alpha ~0.08 to unify magic-hour.
- Truth cells glow warm; manipulator cells glow cold cyan (`#5DECF5`) — injected, alien light.

**Layout (canvas is the hero — NOT a centered 720px column):**
- `<canvas>` is the full-bleed background, the only star; everything else is floating glass HUD (`backdrop-filter: blur(16px)`, semi-transparent `#0B1026`-ish, thin cold border) in the corners.
- Top bar: Cinzel title `VERIDIA` + a generation counter ring.
- Right slide-out **microscope panel**: clicked cell's coordinate → its claim (in pixel-mono) → verdict badge (`TRUTH` warm-gold / `LIE` cold-cyan) → a belief value bar.
- Bottom transport bar: play / step / speed slider + live readouts (`gen 0428`, `truth 61%`, `lie 39%`) in pixel-mono.
- A Cardo "prologue" entry that opens the Genesis intro below.

**Buttons / interaction (root-cause the "fake button" feel — feedback = light brightening/dimming, NOT outlined boxes):**
- idle = misty-white icon, faint glow, low presence.
- hover = brighten + larger glow (`text-shadow 0 0 12px #F6C66B`) + scale 1.05, 200–300ms.
- active/pressed = overexpose to core `#FFE3A8` + scale 0.97 (like lighting a candle).
- selected (mode) = sustained multi-layer halo `#F6C66B` + slow breathing.
- playing = play button sustained glow + slow pulse.
- disabled = muted grey-violet `#8A8FB0`, glow → 0.

**Avoid:** bare Bootstrap/Material/default HTML controls, hard-border boxes to show state, gaussian-blur-only bloom, rounded or anti-aliased cells, plain white or pure-black `#000` backgrounds, candy neon, fast spinners, a vertical centered narrow column.

**Genesis intro to typeset (English, LOCKED — set in Cardo, title in Cinzel):**

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
