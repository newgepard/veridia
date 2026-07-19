import { CAView } from "./ca/CAView";
import "./App.css";

// v0.2 = 复杂科学 CA。本壳只承载前端可视化,Frame 契约由 CAView 消费。
export default function App() {
  return (
    <main className="veridia-app">
      <CAView />
    </main>
  );
}
