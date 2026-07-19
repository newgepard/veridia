import { afterEach, expect, test, vi } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { CanvasField } from "./CanvasField";
import { HONEST, MANIPULATIVE, type Frame } from "./types";

const frame: Frame = {
  step: 0,
  width: 2,
  height: 1,
  belief: [0, 1],
  type: [MANIPULATIVE, HONEST],
  standing: [0.4, 1],
};

afterEach(() => {
  vi.restoreAllMocks();
});

test("draws ASCII glyphs onto the canvas", async () => {
  const fillText = vi.fn();
  const context = {
    canvas: document.createElement("canvas"),
    clearRect: vi.fn(),
    fillRect: vi.fn(),
    fillText,
    putImageData: vi.fn(),
    save: vi.fn(),
    restore: vi.fn(),
    imageSmoothingEnabled: true,
    font: "",
    textAlign: "",
    textBaseline: "",
    globalAlpha: 1,
    globalCompositeOperation: "source-over",
    fillStyle: "",
    filter: "none",
    drawImage: vi.fn(),
  } as unknown as CanvasRenderingContext2D;

  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(context);

  render(<CanvasField frame={frame} />);

  await waitFor(() => {
    expect(fillText).toHaveBeenCalledWith(" ", expect.any(Number), expect.any(Number));
    expect(fillText).toHaveBeenCalledWith("@", expect.any(Number), expect.any(Number));
  });
});
