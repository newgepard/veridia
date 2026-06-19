import { describe, expect, test } from "vitest";
import { LiveEngine } from "./liveEngine";
import { HONEST, MANIPULATIVE } from "./types";

function arrStats(a: number[]) {
  let sum = 0;
  let min = Infinity;
  let max = -Infinity;
  let allFinite = true;
  for (const v of a) {
    if (!Number.isFinite(v)) allFinite = false;
    sum += v;
    if (v < min) min = v;
    if (v > max) max = v;
  }
  const mean = sum / a.length;
  let varAcc = 0;
  for (const v of a) varAcc += (v - mean) * (v - mean);
  return { sum, min, max, mean, variance: varAcc / a.length, allFinite };
}

describe("LiveEngine 忠实移植", () => {
  test("跑 30 步不报错;belief 全程 ∈[0,1] 且有限", () => {
    const eng = new LiveEngine(64, 64, 0);
    for (let i = 0; i < 30; i++) {
      eng.step();
      const f = eng.frame();
      const s = arrStats(f.belief);
      expect(s.allFinite).toBe(true);
      expect(s.min).toBeGreaterThanOrEqual(0);
      expect(s.max).toBeLessThanOrEqual(1);
      expect(f.step).toBe(i + 1);
    }
  });

  test("frame 契约形状:length=W*H、type∈{0,1}、standing∈[0,1]", () => {
    const eng = new LiveEngine(64, 64, 7);
    eng.step();
    const f = eng.frame();
    expect(f.width).toBe(64);
    expect(f.height).toBe(64);
    expect(f.belief.length).toBe(64 * 64);
    expect(f.type.length).toBe(64 * 64);
    expect(f.standing.length).toBe(64 * 64);
    for (const t of f.type) expect(t === HONEST || t === MANIPULATIVE).toBe(true);
    const ss = arrStats(f.standing);
    expect(ss.min).toBeGreaterThanOrEqual(0);
    expect(ss.max).toBeLessThanOrEqual(1);
    expect(ss.allFinite).toBe(true);
  });

  test("结构活着:某中间帧 belief 方差 > 小阈值(非全平)", () => {
    const eng = new LiveEngine(64, 64, 0);
    let maxVar = 0;
    for (let i = 0; i < 30; i++) {
      eng.step();
      const v = arrStats(eng.frame().belief).variance;
      if (v > maxVar) maxVar = v;
    }
    // 全平场方差=0;Orbium 生物存在 → 方差应显著 > 0
    expect(maxVar).toBeGreaterThan(1e-3);
  });

  test("同 seed 确定性:两个引擎跑 30 步后逐帧逐位相同", () => {
    const a = new LiveEngine(64, 64, 42);
    const b = new LiveEngine(64, 64, 42);
    for (let i = 0; i < 30; i++) {
      a.step();
      b.step();
    }
    const fa = a.frame();
    const fb = b.frame();
    expect(fb.belief).toEqual(fa.belief);
    expect(fb.type).toEqual(fa.type);
    expect(fb.standing).toEqual(fa.standing);
  });

  test("不同 seed 产生不同 manipulator 布局", () => {
    const a = new LiveEngine(64, 64, 1).frame();
    const b = new LiveEngine(64, 64, 2).frame();
    expect(b.type).not.toEqual(a.type);
  });

  test("manipulator 比例 ~25%(确定性撒点)", () => {
    const f = new LiveEngine(64, 64, 0).frame();
    const manip = f.type.filter((t) => t === MANIPULATIVE).length;
    const ratio = manip / f.type.length;
    expect(ratio).toBeGreaterThan(0.18);
    expect(ratio).toBeLessThan(0.32);
  });

  test("只读访问器与扁平 frame 一致", () => {
    const eng = new LiveEngine(64, 64, 3);
    eng.step();
    const f = eng.frame();
    const x = 10;
    const y = 12;
    const idx = y * 64 + x;
    expect(eng.beliefAt(x, y)).toBe(f.belief[idx]);
    expect(eng.typeAt(x, y)).toBe(f.type[idx]);
    expect(eng.standingAt(x, y)).toBe(f.standing[idx]);
  });
});
