import "@testing-library/jest-dom";
import { vi } from "vitest";

const canvasContext = {
  canvas: document.createElement("canvas"),
  clearRect: vi.fn(),
  drawImage: vi.fn(),
  fillRect: vi.fn(),
  fillText: vi.fn(),
  putImageData: vi.fn(),
  restore: vi.fn(),
  save: vi.fn(),
  imageSmoothingEnabled: true,
  font: "",
  textAlign: "",
  textBaseline: "",
  globalAlpha: 1,
  globalCompositeOperation: "source-over",
  fillStyle: "",
  filter: "none",
  shadowBlur: 0,
  shadowColor: "",
};

vi.stubGlobal("HTMLCanvasElement", HTMLCanvasElement);
vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(
  canvasContext as unknown as CanvasRenderingContext2D,
);
