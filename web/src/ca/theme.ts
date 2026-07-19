export interface Rgb {
  r: number;
  g: number;
  b: number;
}

export interface AsciiTheme {
  ramp: string;
  honest: [Rgb, Rgb, Rgb];
  manipulative: [Rgb, Rgb, Rgb];
  conflict: [Rgb, Rgb, Rgb];
  minAlpha: number;
  conflictMix: number;
  fontFamily: string;
  background: string;
}

export const VERIDIA_ASCII_THEME: AsciiTheme = {
  ramp: " .·'·:-=+*coe%#@",
  honest: [
    { r: 152, g: 102, b: 88 },
    { r: 209, g: 148, b: 127 },
    { r: 250, g: 222, b: 201 },
  ],
  manipulative: [
    { r: 9, g: 40, b: 78 },
    { r: 41, g: 122, b: 181 },
    { r: 85, g: 173, b: 215 },
  ],
  conflict: [
    { r: 83, g: 55, b: 116 },
    { r: 115, g: 79, b: 144 },
    { r: 202, g: 126, b: 165 },
  ],
  minAlpha: 0.28,
  conflictMix: 0.55,
  fontFamily:
    '"SFMono-Regular", "Menlo", "Consolas", "Liberation Mono", monospace',
  background: "#000001",
};
