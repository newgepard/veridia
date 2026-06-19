import type { Round } from "../types";

const W = 320, H = 120, PAD = 10;

export function TrustChart({ rounds }: { rounds: Round[] }) {
  const n = rounds.length;
  const points = rounds.map((r, i) => {
    const x = n === 1 ? PAD : PAD + (i * (W - 2 * PAD)) / (n - 1);
    const y = H - PAD - r.trust.veridia_to_umbra * (H - 2 * PAD);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return (
    <svg width={W} height={H} className="trust-chart">
      <title>Veridia→Umbra trust over rounds</title>
      <polyline data-testid="trust-line" points={points} fill="none" stroke="currentColor" strokeWidth={2} />
    </svg>
  );
}
