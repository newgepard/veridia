import { MANIPULATIVE, type Frame } from "./types";
import { VERIDIA_ASCII_THEME, type AsciiTheme, type Rgb } from "./theme";

export interface Glyph {
  char: string;
  color: string;
  alpha: number;
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

function mix(a: Rgb, b: Rgb, amount: number): Rgb {
  return {
    r: Math.round(a.r + (b.r - a.r) * amount),
    g: Math.round(a.g + (b.g - a.g) * amount),
    b: Math.round(a.b + (b.b - a.b) * amount),
  };
}

function paletteAt(palette: [Rgb, Rgb, Rgb], value: number): Rgb {
  const scaled = clamp01(value) * 2;
  const index = Math.min(1, Math.floor(scaled));
  return mix(palette[index], palette[index + 1], scaled - index);
}

function rgb({ r, g, b }: Rgb): string {
  return `rgb(${r}, ${g}, ${b})`;
}

export function glyphForBelief(
  belief: number,
  theme: AsciiTheme = VERIDIA_ASCII_THEME,
): string {
  const b = clamp01(belief);
  const index = Math.min(theme.ramp.length - 1, Math.floor(b * theme.ramp.length));
  return theme.ramp[index] ?? " ";
}

export function colorForCell(
  belief: number,
  type: number,
  theme: AsciiTheme = VERIDIA_ASCII_THEME,
): string {
  const b = clamp01(belief);
  const base = paletteAt(type === MANIPULATIVE ? theme.manipulative : theme.honest, b);
  const conflict = paletteAt(theme.conflict, b);
  const uncertainty = Math.max(0, 1 - Math.abs(b - 0.5) * 2);
  return rgb(mix(base, conflict, uncertainty * theme.conflictMix));
}

export function alphaForStanding(
  standing: number,
  theme: AsciiTheme = VERIDIA_ASCII_THEME,
): number {
  const alpha = theme.minAlpha + (1 - theme.minAlpha) * clamp01(standing);
  return Math.round(alpha * 1000) / 1000;
}

export function frameToGlyphs(
  frame: Frame,
  theme: AsciiTheme = VERIDIA_ASCII_THEME,
): Glyph[] {
  const total = frame.width * frame.height;
  const glyphs: Glyph[] = new Array(total);
  for (let i = 0; i < total; i++) {
    const belief = frame.belief[i] ?? 0;
    glyphs[i] = {
      char: glyphForBelief(belief, theme),
      color: colorForCell(belief, frame.type[i] ?? 0, theme),
      alpha: alphaForStanding(frame.standing[i] ?? 0, theme),
    };
  }
  return glyphs;
}
