import type { Round } from "../types";

export function Timeline({ rounds, upto }: { rounds: Round[]; upto: number }) {
  return (
    <div className="timeline">
      {rounds.slice(0, upto + 1).map((r) => (
        <div key={r.round} className="round">
          <h3>Round {r.round} — V:{r.actions.veridia} / U:{r.actions.umbra}</h3>
          {r.messages.map((m, i) => (
            <div key={i} data-testid="msg" className={`msg ${m.from}`}>
              <strong>{m.from}</strong>
              {m.channel === "dm" ? <em> [dm]</em> : null}
              {m.verdict ? <span className={`badge ${m.verdict}`}> {m.verdict}</span> : null}
              <span>: {m.text}</span>
            </div>
          ))}
          {r.flags.length ? <small className="flags">⚑ {r.flags.join(", ")}</small> : null}
        </div>
      ))}
    </div>
  );
}
