import type { Trace } from "../types";

export function Scoreboard({ trace }: { trace: Trace }) {
  const { veridia, umbra } = trace.metrics.final_scores as { veridia: number; umbra: number };
  return (
    <div className="scoreboard">
      <h2>Winner: <span data-testid="winner">{trace.winner}</span></h2>
      <p>Veridia {veridia?.toFixed(1)} · Umbra {umbra?.toFixed(1)}</p>
      <p>Lies: <span data-testid="lie-count">{trace.metrics.lie_count}</span> · Detected: {trace.metrics.lies_detected}</p>
    </div>
  );
}
