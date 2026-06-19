import { describe, expect, test } from "vitest";
import {
  DEFAULT_LENIA_PARAMS,
  leniaStep,
  makeKernel,
  seedOrbium,
  type Grid,
} from "./lenia";

function stats(data: Float32Array) {
  let sum = 0;
  let min = Infinity;
  let max = -Infinity;
  let allFinite = true;
  for (const v of data) {
    if (!Number.isFinite(v)) allFinite = false;
    sum += v;
    if (v < min) min = v;
    if (v > max) max = v;
  }
  return { sum, min, max, mean: sum / data.length, allFinite };
}

describe("lenia kernel", () => {
  test("环形高斯核已归一化(和≈1),尺寸=2R+1", () => {
    const k = makeKernel(DEFAULT_LENIA_PARAMS);
    expect(k.size).toBe(2 * DEFAULT_LENIA_PARAMS.R + 1);
    const s = stats(k.data);
    expect(s.sum).toBeCloseTo(1.0, 6);
    expect(s.min).toBeGreaterThanOrEqual(0);
  });

  test("半径>1 处核值被截断为 0(角落)", () => {
    const k = makeKernel(DEFAULT_LENIA_PARAMS);
    // 左上角 (0,0) 对应 (dx,dy)=(-R,-R),归一化半径=√2>1,应为 0
    expect(k.data[0]).toBe(0);
  });
});

describe("seedOrbium", () => {
  test("播种非空且全程 ∈[0,1]", () => {
    const g = seedOrbium(64, 64);
    expect(g.width).toBe(64);
    expect(g.height).toBe(64);
    const s = stats(g.data);
    expect(s.sum).toBeGreaterThan(0); // 有 Orbium 质量
    expect(s.min).toBeGreaterThanOrEqual(0);
    expect(s.max).toBeLessThanOrEqual(1);
    expect(s.max).toBeGreaterThan(0.5); // Orbium 内部有接近 1 的格
  });
});

describe("leniaStep", () => {
  test("单步后场仍 ∈[0,1] 且有限", () => {
    const g = seedOrbium(64, 64);
    const next = leniaStep(g);
    const s = stats(next.data);
    expect(s.allFinite).toBe(true);
    expect(s.min).toBeGreaterThanOrEqual(0);
    expect(s.max).toBeLessThanOrEqual(1);
  });

  test("不就地修改入参", () => {
    const g = seedOrbium(64, 64);
    const before = g.data.slice();
    leniaStep(g);
    expect(Array.from(g.data)).toEqual(Array.from(before));
  });

  test("跑 30 步:结构活着(非全 0)、全程有界、同核确定性", () => {
    const kernel = makeKernel(DEFAULT_LENIA_PARAMS);
    let g: Grid = seedOrbium(64, 64);
    for (let i = 0; i < 30; i++) {
      g = leniaStep(g, DEFAULT_LENIA_PARAMS, kernel);
      const s = stats(g.data);
      expect(s.allFinite).toBe(true);
      expect(s.min).toBeGreaterThanOrEqual(0);
      expect(s.max).toBeLessThanOrEqual(1);
    }
    const after = stats(g.data);
    expect(after.sum).toBeGreaterThan(0.5); // 没有抹平成全 0,生物仍活着

    // 同核同种子,重跑 30 步应逐位相同(确定性)
    let g2: Grid = seedOrbium(64, 64);
    for (let i = 0; i < 30; i++) g2 = leniaStep(g2, DEFAULT_LENIA_PARAMS, kernel);
    expect(Array.from(g2.data)).toEqual(Array.from(g.data));
  });
});
