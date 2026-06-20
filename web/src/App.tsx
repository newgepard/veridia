import { CAView } from "./ca/CAView";

// v0.1 仪表盘(晶族 vs 雾族 1v1 谈判 Scoreboard/Timeline/TrustChart)已移除;
// v0.2 = 复杂科学 CA,本壳只渲染 CAView。
export default function App() {
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", fontFamily: "sans-serif" }}>
      <h1>Veridia — 晶族 vs 雾族</h1>
      <CAView />
    </main>
  );
}
