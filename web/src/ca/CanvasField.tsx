import { useEffect, useRef } from "react";
import type { Frame } from "./types";
import { MANIPULATIVE } from "./types";

// 把一帧画到 <canvas>:belief 主通道(暖=真亮/冷=谎暗),standing 调亮度,type 染色。
// 复杂科学要看涌现结构,所以逐格上色、不做平均/扩散。

interface Props {
  frame: Frame;
}

function clamp01(v: number): number {
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

// belief: 0(谎/冷暗)->1(真/暖亮)。返回 [r,g,b]。
function colormap(belief: number): [number, number, number] {
  const b = clamp01(belief);
  // 冷端(蓝青) -> 暖端(橙金):线性插值。
  const cold: [number, number, number] = [20, 40, 90];
  const warm: [number, number, number] = [255, 190, 70];
  return [
    cold[0] + (warm[0] - cold[0]) * b,
    cold[1] + (warm[1] - cold[1]) * b,
    cold[2] + (warm[2] - cold[2]) * b,
  ];
}

export function frameToImageData(frame: Frame): ImageData {
  const { width, height, belief, type, standing } = frame;
  const data = new Uint8ClampedArray(width * height * 4);
  for (let i = 0; i < width * height; i++) {
    let [r, g, b] = colormap(belief[i] ?? 0);
    // standing 调亮度:站位低则压暗(下限 0.35 保证仍可见)。
    const bright = 0.35 + 0.65 * clamp01(standing[i] ?? 0);
    r *= bright;
    g *= bright;
    b *= bright;
    // type 染色:操纵者偏品红,诚实者偏青绿,轻微 tint。
    if ((type[i] ?? 0) === MANIPULATIVE) {
      r = r * 0.85 + 255 * 0.15;
      b = b * 0.85 + 120 * 0.15;
    } else {
      g = g * 0.9 + 200 * 0.1;
    }
    const o = i * 4;
    data[o] = r;
    data[o + 1] = g;
    data[o + 2] = b;
    data[o + 3] = 255;
  }
  return new ImageData(data, width, height);
}

export function CanvasField({ frame }: Props) {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return; // jsdom 下无 2d 上下文,跳过绘制。
    ctx.putImageData(frameToImageData(frame), 0, 0);
  }, [frame]);

  return (
    <canvas
      ref={ref}
      data-testid="ca-canvas"
      width={frame.width}
      height={frame.height}
      style={{
        width: "100%",
        maxWidth: 480,
        imageRendering: "pixelated",
        border: "1px solid #333",
        display: "block",
      }}
    />
  );
}
