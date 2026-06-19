import { useState } from "react";
import trace from "./fixtures/sample-trace.json";
import type { Trace } from "./types";
import { Scoreboard } from "./components/Scoreboard";
import { Timeline } from "./components/Timeline";
import { TrustChart } from "./components/TrustChart";
import { CAView } from "./ca/CAView";

const t = trace as Trace;

export default function App() {
  const [cursor, setCursor] = useState(0);
  const max = t.rounds.length - 1;
  return (
    <main style={{ maxWidth: 720, margin: "0 auto", fontFamily: "sans-serif" }}>
      <h1>Veridia — 晶族 vs 雾族</h1>
      <Scoreboard trace={t} />
      <TrustChart rounds={t.rounds} />
      <input
        type="range" data-testid="cursor" min={0} max={max} value={cursor}
        onChange={(e) => setCursor(Number(e.target.value))}
      />
      <p>Round {cursor + 1} / {t.rounds.length}</p>
      <Timeline rounds={t.rounds} upto={cursor} />
      <hr style={{ margin: "32px 0", border: 0, borderTop: "1px solid #ddd" }} />
      <CAView />
    </main>
  );
}
