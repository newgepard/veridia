// LiveEngine —— 浏览器端实时 CA 引擎,忠实移植 ca/rule.py + ca/engine.py。
//
// 每步:Lenia 更新 belief 场(连续涌现,来自 lenia.ts) + 语义本地规则更新
// belief 微调 + standing。.frame() 把当前态导成契约 Frame(同 web/src/ca/types.ts 形状)。
//
// 无 LLM、确定性 given seed。
//
// 关于"对得上 Python 行为":转移函数(Lenia step、honest/manip nudge、带符号 standing
// 规则)与 rule.py/engine.py 逐式一致。唯一无法逐位复刻的是随机源——Python 用
// numpy 的 PCG64(np.random.default_rng),JS 没有等价实现;这里用确定性的 mulberry32,
// 保证:① 微噪声幅度 0.02、② manipulator 比例 ~25%、③ 同 seed 完全可复现。
// 这些是规则的统计性质,不是逐格数值身份,符合"忠实移植行为 + 确定性"的要求。

import type { Frame } from "./types";
import { HONEST, MANIPULATIVE } from "./types";
import {
  DEFAULT_LENIA_PARAMS,
  leniaStep,
  makeKernel,
  seedOrbium,
  type Grid,
  type Kernel,
  type LeniaParams,
} from "./lenia";

// 真/谎规则参数,对应 rule.py 的 RuleParams。
export interface RuleParams {
  F: number; // 真相吸引子
  honestPull: number; // 诚实格朝 F 的微调强度
  manipPush: number; // 操纵者格推离 F 的强度
  eta: number; // standing 学习率
  liePole: number; // 操纵者发射的谎言极
}

export const DEFAULT_RULE_PARAMS: RuleParams = {
  F: 1.0,
  honestPull: 0.05,
  manipPush: 0.05,
  eta: 0.1,
  liePole: 0.0,
};

function clamp01(v: number): number {
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

// 确定性 PRNG(mulberry32):种子化、可复现,用于撒噪声与 manipulator。
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// 对每格,取其 8 邻域中 mask=True 的格上 field 的均值(环面)。
// 无满足条件的邻居时该格取 0。对应 rule.py 的 _neighbor_mean。
function neighborMeanMasked(
  field: Float32Array,
  mask: Uint8Array,
  W: number,
  H: number,
): Float32Array {
  const out = new Float32Array(W * H);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      let sum = 0;
      let cnt = 0;
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          if (dx === 0 && dy === 0) continue;
          const sy = (((y + dy) % H) + H) % H;
          const sx = (((x + dx) % W) + W) % W;
          const idx = sy * W + sx;
          if (mask[idx]) {
            sum += field[idx];
            cnt += 1;
          }
        }
      }
      out[y * W + x] = cnt > 0 ? sum / cnt : 0;
    }
  }
  return out;
}

export class LiveEngine {
  readonly width: number;
  readonly height: number;
  readonly seed: number;
  stepCount: number;

  private lenia: LeniaParams;
  private rule: RuleParams;
  private kernel: Kernel;

  private belief: Float32Array; // height*width 行优先, ∈[0,1]
  private type: Uint8Array; // 0=honest 1=manipulator, 固定不变
  private standing: Float32Array; // ∈[0,1]

  constructor(
    width: number,
    height: number,
    seed = 0,
    params?: { lenia?: Partial<LeniaParams>; rule?: Partial<RuleParams> },
  ) {
    this.width = width | 0;
    this.height = height | 0;
    this.seed = seed | 0;
    this.stepCount = 0;
    this.lenia = { ...DEFAULT_LENIA_PARAMS, ...(params?.lenia ?? {}) };
    this.rule = { ...DEFAULT_RULE_PARAMS, ...(params?.rule ?? {}) };
    this.kernel = makeKernel(this.lenia);

    const W = this.width;
    const H = this.height;
    const rng = mulberry32(this.seed);

    // belief 场:放一只 Orbium("生物"),保证活的可滑行涌现结构(对应 engine.py)。
    const seeded: Grid = seedOrbium(W, H);
    this.belief = seeded.data;
    // 加一点确定性噪声让场不至于全 0、也让多 seed 有差异,但不淹没 Orbium(幅度 0.02)。
    for (let i = 0; i < this.belief.length; i++) {
      this.belief[i] = clamp01(this.belief[i] + rng() * 0.02);
    }

    // type 场:确定性地按种子撒操纵者(约 25%),固定不变(对应 engine.py)。
    this.type = new Uint8Array(W * H);
    for (let i = 0; i < this.type.length; i++) {
      this.type[i] = rng() < 0.25 ? MANIPULATIVE : HONEST;
    }

    // standing 场:从中性 0.5 起。
    this.standing = new Float32Array(W * H).fill(0.5);
  }

  // 每格发射的 claim c:诚实=自身 belief,操纵者=谎言极。对应 rule.py 的 emitted_claim。
  private emittedClaim(): Float32Array {
    const c = new Float32Array(this.belief.length);
    for (let i = 0; i < c.length; i++) {
      c[i] = this.type[i] === MANIPULATIVE ? this.rule.liePole : this.belief[i];
    }
    return c;
  }

  // 语义本地规则对 belief 的微调:诚实朝 F,操纵者离 F。对应 rule.py 的 belief_update。
  private beliefUpdate(): void {
    const { F, honestPull, manipPush } = this.rule;
    const b = this.belief;
    for (let i = 0; i < b.length; i++) {
      let delta: number;
      if (this.type[i] === HONEST) {
        delta = honestPull * (F - b[i]); // 朝 F 拉
      } else {
        delta = manipPush * (b[i] - F); // 推离 F(沿 b-F 放大)
      }
      b[i] = clamp01(b[i] + delta);
    }
  }

  // LOCKED 带符号可信度规则:standing 演化(用更新后的 belief)。对应 rule.py 的 standing_update。
  // 对每格,把其 claim c 拿去和"诚实邻居的 belief b_h"对账:贡献 = b_h*(1-2|c-b_h|),
  // 取邻域均值乘 eta 累加到 standing,clamp 到 [0,1]。
  private standingUpdate(): void {
    const W = this.width;
    const H = this.height;
    const c = this.emittedClaim();

    // 诚实邻居的 belief 均值 b_h(每格视角)
    const honestMask = new Uint8Array(this.type.length);
    for (let i = 0; i < honestMask.length; i++) {
      honestMask[i] = this.type[i] === HONEST ? 1 : 0;
    }
    const bh = neighborMeanMasked(this.belief, honestMask, W, H);

    for (let i = 0; i < this.standing.length; i++) {
      const signal = bh[i] * (1.0 - 2.0 * Math.abs(c[i] - bh[i]));
      this.standing[i] = clamp01(this.standing[i] + this.rule.eta * signal);
    }
  }

  // 推进一帧:Lenia(belief) → 语义规则(belief 微调) → standing。对应 engine.py 的 step。
  step(): void {
    // 1) 复杂科学层:Lenia 连续更新(直接卷积、环面、∈[0,1])
    const next = leniaStep(
      { width: this.width, height: this.height, data: this.belief },
      this.lenia,
      this.kernel,
    );
    this.belief = next.data;
    // 2) 语义本地规则:真/谎对 belief 的微调
    this.beliefUpdate();
    // 3) 带符号可信度规则:standing 演化(用更新后的 belief)
    this.standingUpdate();
    this.stepCount += 1;
  }

  // 导出当前态为契约 Frame(行优先扁平化)。对应 engine.py 的 frame()。
  frame(): Frame {
    return {
      step: this.stepCount,
      width: this.width,
      height: this.height,
      belief: Array.from(this.belief),
      type: Array.from(this.type),
      standing: Array.from(this.standing),
    };
  }

  // 只读访问器:供前端点击判读用(不暴露内部可变数组)。
  beliefAt(x: number, y: number): number {
    return this.belief[y * this.width + x];
  }
  typeAt(x: number, y: number): number {
    return this.type[y * this.width + x];
  }
  standingAt(x: number, y: number): number {
    return this.standing[y * this.width + x];
  }
}
