import type { MicroscopeRecord } from "./types";

// 显微镜面板:展示某个被点开的格子的语义判读(claim/verdict/reason)。
// LLM 只读、只在这一层落字,从不写回 CA。

interface Props {
  record: MicroscopeRecord | null;
}

export function MicroscopePanel({ record }: Props) {
  if (!record) {
    return (
      <div data-testid="microscope-panel" style={{ padding: 12, color: "#888" }}>
        点一个格子,看显微镜下它说了什么。
      </div>
    );
  }

  const isLie = record.verdict === "lie";
  return (
    <div data-testid="microscope-panel" style={{ padding: 12 }}>
      <div style={{ fontSize: 12, color: "#888", marginBottom: 4 }}>
        cell ({record.x}, {record.y}) · step {record.step}
      </div>
      <blockquote
        data-testid="microscope-claim"
        style={{ margin: "0 0 8px", fontStyle: "italic" }}
      >
        “{record.claim}”
      </blockquote>
      <span
        data-testid="microscope-verdict"
        style={{
          display: "inline-block",
          padding: "2px 10px",
          borderRadius: 999,
          fontSize: 12,
          fontWeight: 600,
          color: "#fff",
          background: isLie ? "#c0392b" : "#1e8449",
        }}
      >
        {isLie ? "lie" : "truthful"}
      </span>
      <p data-testid="microscope-reason" style={{ marginTop: 8, color: "#444" }}>
        {record.reason}
      </p>
    </div>
  );
}
