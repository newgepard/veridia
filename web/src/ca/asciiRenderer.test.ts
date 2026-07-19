import { describe, expect, test } from "vitest";
import { frameToGlyphs } from "./asciiRenderer";
import { VERIDIA_ASCII_THEME } from "./theme";
import { HONEST, MANIPULATIVE, type Frame } from "./types";

function frame(overrides: Partial<Frame> = {}): Frame {
  return {
    step: 0,
    width: 3,
    height: 1,
    belief: [0, 0.5, 1],
    type: [MANIPULATIVE, HONEST, HONEST],
    standing: [0, 0.5, 1],
    ...overrides,
  };
}

describe("frameToGlyphs", () => {
  test("returns one glyph per frame cell", () => {
    const glyphs = frameToGlyphs(frame());
    expect(glyphs).toHaveLength(3);
  });

  test("maps stronger belief to denser ASCII characters", () => {
    const glyphs = frameToGlyphs(frame());
    const ramp = VERIDIA_ASCII_THEME.ramp;

    expect(ramp.indexOf(glyphs[0].char)).toBeLessThan(ramp.indexOf(glyphs[1].char));
    expect(ramp.indexOf(glyphs[1].char)).toBeLessThan(ramp.indexOf(glyphs[2].char));
  });

  test("uses cold colors for manipulative cells and warm colors for honest cells", () => {
    const glyphs = frameToGlyphs(frame());

    expect(glyphs[0].color).toBe("rgb(9, 40, 78)");
    expect(glyphs[2].color).toBe("rgb(250, 222, 201)");
  });

  test("pushes uncertain middle belief toward the conflict palette", () => {
    const glyphs = frameToGlyphs(frame());

    expect(glyphs[1].color).toBe("rgb(157, 110, 136)");
  });

  test("maps standing to alpha without making low-standing cells disappear", () => {
    const glyphs = frameToGlyphs(frame());

    expect(glyphs[0].alpha).toBeGreaterThan(0);
    expect(glyphs[0].alpha).toBeLessThan(glyphs[1].alpha);
    expect(glyphs[1].alpha).toBeLessThan(glyphs[2].alpha);
    expect(glyphs[2].alpha).toBe(1);
  });
});
