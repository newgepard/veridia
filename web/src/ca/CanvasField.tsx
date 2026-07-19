import { useEffect, useRef } from "react";
import type { Frame } from "./types";
import { frameToGlyphs } from "./asciiRenderer";
import { VERIDIA_ASCII_THEME } from "./theme";

interface Props {
  frame: Frame;
}

function cellSizeFor(frame: Frame): number {
  return frame.width >= 60 || frame.height >= 60 ? 10 : 12;
}

export function CanvasField({ frame }: Props) {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const cellSize = cellSizeFor(frame);
    const width = frame.width * cellSize;
    const height = frame.height * cellSize;
    if (canvas.width !== width) canvas.width = width;
    if (canvas.height !== height) canvas.height = height;

    const draw = () => {
      const glyphs = frameToGlyphs(frame);

      ctx.save();
      ctx.imageSmoothingEnabled = false;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = VERIDIA_ASCII_THEME.background;
      ctx.fillRect(0, 0, width, height);
      ctx.font = `${Math.round(cellSize * 1.08)}px ${VERIDIA_ASCII_THEME.fontFamily}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.globalCompositeOperation = "lighter";

      for (let i = 0; i < glyphs.length; i++) {
        const glyph = glyphs[i];
        const x = i % frame.width;
        const y = Math.floor(i / frame.width);
        const px = x * cellSize + cellSize / 2;
        const py = y * cellSize + cellSize / 2;
        ctx.globalAlpha = glyph.alpha;
        ctx.fillStyle = glyph.color;
        ctx.shadowColor = glyph.color;
        ctx.shadowBlur = 7;
        ctx.fillText(glyph.char, px, py);
      }

      ctx.restore();
    };

    const raf =
      typeof window.requestAnimationFrame === "function"
        ? window.requestAnimationFrame(draw)
        : window.setTimeout(draw, 0);
    return () => {
      if (typeof window.cancelAnimationFrame === "function") {
        window.cancelAnimationFrame(raf);
      } else {
        window.clearTimeout(raf);
      }
    };
  }, [frame]);

  const cellSize = cellSizeFor(frame);

  return (
    <canvas
      ref={ref}
      data-testid="ca-canvas"
      aria-label="Veridia ASCII belief field"
      className="ca-ascii-canvas"
      width={frame.width * cellSize}
      height={frame.height * cellSize}
    />
  );
}
