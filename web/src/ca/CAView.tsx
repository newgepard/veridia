import { useEffect, useMemo, useRef, useState } from "react";
import type { CATrace, MicroscopeRecord } from "./types";
import { CanvasField } from "./CanvasField";
import { MicroscopePanel } from "./MicroscopePanel";
import rawTrace from "./fixtures/run-trace.json";
// 集成阶段已把 import 换成 run-trace.json(真引擎+显微镜产物),形状一致。

const trace = rawTrace as unknown as CATrace;

// 在 microscope 列表里,找与点击格子(step,x,y)最近的一条记录。
function nearestRecord(
  records: MicroscopeRecord[],
  step: number,
  x: number,
  y: number,
): MicroscopeRecord | null {
  if (records.length === 0) return null;
  let best: MicroscopeRecord | null = null;
  let bestD = Infinity;
  for (const r of records) {
    // 同步优先:先按 step 距离,再按格子欧氏距离平方。
    const ds = Math.abs(r.step - step);
    const dd = (r.x - x) * (r.x - x) + (r.y - y) * (r.y - y);
    const d = ds * 100000 + dd;
    if (d < bestD) {
      bestD = d;
      best = r;
    }
  }
  return best;
}

export function CAView() {
  const frames = trace.frames;
  const maxStep = frames.length - 1;
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selected, setSelected] = useState<MicroscopeRecord | null>(null);

  const frame = frames[Math.min(step, maxStep)];

  // 播放:推进 step,到末尾停。
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setStep((s) => {
        if (s >= maxStep) {
          setPlaying(false);
          return s;
        }
        return s + 1;
      });
    }, 200);
    return () => clearInterval(id);
  }, [playing, maxStep]);

  const canvasWrapRef = useRef<HTMLDivElement | null>(null);

  function handleClick(e: React.MouseEvent<HTMLDivElement>) {
    const canvas = canvasWrapRef.current?.querySelector("canvas");
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    const x = Math.floor(((e.clientX - rect.left) / rect.width) * frame.width);
    const y = Math.floor(((e.clientY - rect.top) / rect.height) * frame.height);
    const cx = Math.max(0, Math.min(frame.width - 1, x));
    const cy = Math.max(0, Math.min(frame.height - 1, y));
    setSelected(nearestRecord(trace.microscope, step, cx, cy));
  }

  const verdictCount = useMemo(() => trace.microscope.length, []);

  return (
    <section data-testid="ca-view" style={{ marginTop: 32 }}>
      <h2>Veridia CA — 涌现的真相场</h2>
      <p style={{ color: "#888", fontSize: 13 }}>
        game {trace.game_id} · {frames.length} 帧 · {verdictCount} 条显微镜记录
      </p>

      <div ref={canvasWrapRef} onClick={handleClick} style={{ cursor: "crosshair" }}>
        <CanvasField frame={frame} />
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12 }}>
        <button
          data-testid="ca-play"
          onClick={() => {
            if (step >= maxStep) setStep(0);
            setPlaying((p) => !p);
          }}
        >
          {playing ? "暂停" : "播放"}
        </button>
        <input
          type="range"
          data-testid="ca-step"
          min={0}
          max={maxStep}
          value={step}
          onChange={(e) => {
            setPlaying(false);
            setStep(Number(e.target.value));
          }}
          style={{ flex: 1 }}
        />
        <span data-testid="ca-step-label">
          step {frame.step} / {maxStep}
        </span>
      </div>

      <MicroscopePanel record={selected} />
    </section>
  );
}
