import { render, screen } from "@testing-library/react";
import { Timeline } from "./Timeline";
import trace from "../fixtures/sample-trace.json";
import type { Trace } from "../types";

test("renders messages up to cursor only", () => {
  const t = trace as Trace;
  render(<Timeline rounds={t.rounds} upto={0} />);
  const shown = screen.getAllByTestId("msg");
  expect(shown.length).toBe(t.rounds[0].messages.length); // only round 0
});
