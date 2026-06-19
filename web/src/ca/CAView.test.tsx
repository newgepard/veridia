import { render, screen, fireEvent } from "@testing-library/react";
import { CAView } from "./CAView";

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
  expect(screen.getByTestId("microscope-panel")).toHaveTextContent(/点一个格子/);
});
