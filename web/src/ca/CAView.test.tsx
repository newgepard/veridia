import { render, screen, fireEvent } from "@testing-library/react";
import { CAView } from "./CAView";
import { readCellOffline } from "./liveEngine";
import { HONEST, MANIPULATIVE } from "./types";

// ---- 回放模式(默认):v0.1/v0.2 行为不破 ----

test("renders the CA canvas", () => {
  render(<CAView />);
  expect(screen.getByTestId("ca-canvas")).toBeInTheDocument();
});

test("step slider is present and changes the rendered step", () => {
  render(<CAView />);
  const slider = screen.getByTestId("ca-step") as HTMLInputElement;
  expect(slider).toBeInTheDocument();

  const label = screen.getByTestId("ca-step-label");
  const before = label.textContent;

  // 拖到末尾,渲染的 step 标签应当变化。
  fireEvent.change(slider, { target: { value: slider.max } });
  expect(label.textContent).not.toBe(before);
  expect(slider.value).toBe(slider.max);
});

test("microscope panel shows a hint when nothing is selected", () => {
  render(<CAView />);
  expect(screen.getByTestId("microscope-panel")).toHaveTextContent(/click any cell/i);
});

// ---- 模式切换 + 实时模式 ----

test("默认是回放模式,有模式切换按钮", () => {
  render(<CAView />);
  expect(screen.getByTestId("ca-shell-title")).toHaveTextContent("VERIDIA");
  expect(screen.getByTestId("ca-mode-replay")).toBeInTheDocument();
  expect(screen.getByTestId("ca-mode-live")).toBeInTheDocument();
  expect(screen.getByTestId("ca-mode-replay")).toHaveTextContent("REPLAY");
  expect(screen.getByTestId("ca-mode-live")).toHaveTextContent("LIVE");
  // 默认回放:回放滑块在场
  expect(screen.getByTestId("ca-step")).toBeInTheDocument();
});

test("切到实时模式:canvas 在场、有 live 播放/单步,单步推进 step 标签", () => {
  render(<CAView />);
  fireEvent.click(screen.getByTestId("ca-mode-live"));

  expect(screen.getByTestId("ca-canvas")).toBeInTheDocument();
  expect(screen.getByTestId("ca-live-play")).toBeInTheDocument();

  const label = screen.getByTestId("ca-live-step-label");
  expect(label.textContent).toBe("step 0");
  fireEvent.click(screen.getByTestId("ca-live-step"));
  expect(label.textContent).toBe("step 1");
  fireEvent.click(screen.getByTestId("ca-live-step"));
  expect(label.textContent).toBe("step 2");
});

test("实时模式重置回 step 0", () => {
  render(<CAView />);
  fireEvent.click(screen.getByTestId("ca-mode-live"));
  fireEvent.click(screen.getByTestId("ca-live-step"));
  expect(screen.getByTestId("ca-live-step-label").textContent).toBe("step 1");
  fireEvent.click(screen.getByTestId("ca-live-reset"));
  expect(screen.getByTestId("ca-live-step-label").textContent).toBe("step 0");
});

test("切回回放模式仍可用", () => {
  render(<CAView />);
  fireEvent.click(screen.getByTestId("ca-mode-live"));
  fireEvent.click(screen.getByTestId("ca-mode-replay"));
  expect(screen.getByTestId("ca-step")).toBeInTheDocument();
  expect(screen.getByTestId("microscope-panel")).toHaveTextContent(/click any cell/i);
});

// ---- 确定性离线判读模板:方向正确 ----

test("readCellOffline:manipulator → lie(无论 belief)", () => {
  const r = readCellOffline(MANIPULATIVE, 0.9, 3, 4, 7);
  expect(r.verdict).toBe("lie");
  expect(r.x).toBe(3);
  expect(r.y).toBe(4);
  expect(r.step).toBe(7);
  expect(r.claim.length).toBeGreaterThan(0);
});

test("readCellOffline:honest → truthful,reason 反映 belief 百分比", () => {
  const hi = readCellOffline(HONEST, 0.95, 0, 0, 1);
  expect(hi.verdict).toBe("truthful");
  expect(hi.reason).toContain("95%");

  const lo = readCellOffline(HONEST, 0.05, 0, 0, 1);
  expect(lo.verdict).toBe("truthful");
  expect(lo.reason).toContain("5%");
});
