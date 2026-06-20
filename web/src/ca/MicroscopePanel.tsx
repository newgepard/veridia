import type { MicroscopeRecord } from "./types";

// 显微镜面板:展示某个被点开的格子的语义判读(claim/verdict/reason)。
// LLM 只读、只在这一层落字,从不写回 CA。

interface Props {
  record: MicroscopeRecord | null;
}

export function MicroscopePanel({ record }: Props) {
  if (!record) {
    return (
      <aside data-testid="microscope-panel" className="microscope-panel is-empty">
        <div className="microscope-heading">CONSTITUTIONAL COURT</div>
        <p>click any cell to convene the court</p>
        <span className="microscope-cursor" aria-hidden="true">
          |
        </span>
      </aside>
    );
  }

  const isLie = record.verdict === "lie";
  return (
    <aside data-testid="microscope-panel" className="microscope-panel">
      <div className="microscope-heading">CONSTITUTIONAL COURT</div>
      <div className="microscope-meta">
        cell ({record.x}, {record.y}) / step {record.step}
      </div>
      <div className="microscope-row">
        <span className="microscope-key">claim:</span>
        <q data-testid="microscope-claim">{record.claim}</q>
      </div>
      <div className="microscope-row">
        <span className="microscope-key">verdict:</span>
        <span
          data-testid="microscope-verdict"
          className={isLie ? "microscope-verdict is-lie" : "microscope-verdict is-truthful"}
        >
          {isLie ? "LIE" : "TRUTHFUL"}
        </span>
      </div>
      <p data-testid="microscope-reason" className="microscope-reason">
        {record.reason}
      </p>
    </aside>
  );
}
