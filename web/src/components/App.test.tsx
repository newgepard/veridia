import { render, screen, fireEvent } from "@testing-library/react";
import App from "../App";

test("cursor controls timeline length", () => {
  render(<App />);
  const slider = screen.getByTestId("cursor") as HTMLInputElement;
  const initial = screen.getAllByTestId("msg").length;
  fireEvent.change(slider, { target: { value: slider.max } });
  expect(screen.getAllByTestId("msg").length).toBeGreaterThanOrEqual(initial);
  expect(screen.getByTestId("winner")).toBeInTheDocument();
});
