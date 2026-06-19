import { render, screen } from "@testing-library/react";
import { TrustChart } from "./TrustChart";
import trace from "../fixtures/sample-trace.json";
import type { Trace } from "../types";

test("plots one point per round", () => {
  const t = trace as Trace;
  render(<TrustChart rounds={t.rounds} />);
  const line = screen.getByTestId("trust-line");
  const pts = line.getAttribute("points")!.trim().split(/\s+/);
  expect(pts.length).toBe(t.rounds.length);
});
