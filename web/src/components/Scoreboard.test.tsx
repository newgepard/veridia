import { render, screen } from "@testing-library/react";
import { Scoreboard } from "./Scoreboard";
import trace from "../fixtures/sample-trace.json";
import type { Trace } from "../types";

test("shows winner and lie count", () => {
  render(<Scoreboard trace={trace as Trace} />);
  expect(screen.getByText(/winner/i)).toBeInTheDocument();
  expect(screen.getByTestId("lie-count")).toHaveTextContent(String((trace as Trace).metrics.lie_count));
});
