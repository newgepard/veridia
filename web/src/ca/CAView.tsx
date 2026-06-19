import { useEffect, useMemo, useRef, useState } from "react";
import type { CATrace, Frame, MicroscopeRecord } from "./types";
import { CanvasField } from "./CanvasField";
import { MicroscopePanel } from "./MicroscopePanel";
import { LiveEngine, readCellOffline } from "./liveEngine";
import rawTrace from "./fixtures/run-trace.json";
// 集成阶段已把 import 换成 run-trace.json(真引擎+显微镜产物),形状一致。

const trace = rawTrace as unknown as CATrace;

// 实时模式网格尺寸(64² 直接卷积流畅)。
const LIVE_W = 64;
const LIVE_H = 64;
const LIVE_SEED = 0;

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
  const [mode, setMode] = useState<"replay" | "live">("replay");
  return (
    <section data-testid="ca-view" style={{ marginTop: 32 }}>
      <h2>Veridia CA — 涌现的真相场</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <button
          data-testid="ca-mode-replay"
          onClick={() => setMode("replay")}
          style={{ fontWeight: mode === "replay" ? 700 : 400 }}
        >
          回放(trace)
        </button>
        <button
          data-testid="ca-mode-live"
          onClick={() => setMode("live")}
          style={{ fontWeight: mode === "live" ? 700 : 400 }}
        >
          实时(LiveEngine)
        </button>
      </div>
      {mode === "replay" ? <ReplayView /> : <LiveView />}
    </section>
  );
}

// 回放模式:读 run-trace.json,行为与 v0.1/v0.2 一致(LLM 显微镜记录)。
function ReplayView() {
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
    <>
      <p style={{ color: "#888", fontSize: 13 }}>
        回放 · game {trace.game_id} · {frames.length} 帧 · {verdictCount} 条显微镜记录
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
    </>
  );
}

// 实时模式:浏览器里跑 LiveEngine,requestAnimationFrame/setInterval 不断 step+重渲。
// 点击 → 确定性离线判读模板(不调 LLM)。
function LiveView() {
  const engineRef = useRef<LiveEngine | null>(null);
  if (engineRef.current === null) {
    engineRef.current = new LiveEngine(LIVE_W, LIVE_H, LIVE_SEED);
  }
  const [frame, setFrame] = useState<Frame>(() => engineRef.current!.frame());
  const [playing, setPlaying] = useState(false);
  const [selected, setSelected] = useState<MicroscopeRecord | null>(null);

  // 播放:不断 step + 重渲(经 CanvasField)。暂停即停。
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      const eng = engineRef.current;
      if (!eng) return;
      eng.step();
      setFrame(eng.frame());
    }, 120);
    return () => clearInterval(id);
  }, [playing]);

  const canvasWrapRef = useRef<HTMLDivElement | null>(null);

  function handleClick(e: React.MouseEvent<HTMLDivElement>) {
    const eng = engineRef.current;
    if (!eng) return;
    const canvas = canvasWrapRef.current?.querySelector("canvas");
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    const x = Math.floor(((e.clientX - rect.left) / rect.width) * frame.width);
    const y = Math.floor(((e.clientY - rect.top) / rect.height) * frame.height);
    const cx = Math.max(0, Math.min(frame.width - 1, x));
    const cy = Math.max(0, Math.min(frame.height - 1, y));
    // 确定性 TS 模板判读:从该 cell 的 type/belief 算 claim+verdict+reason。
    setSelected(readCellOffline(eng.typeAt(cx, cy), eng.beliefAt(cx, cy), cx, cy, frame.step));
  }

  function reset() {
    setPlaying(false);
    const eng = new LiveEngine(LIVE_W, LIVE_H, LIVE_SEED);
    engineRef.current = eng;
    setFrame(eng.frame());
    setSelected(null);
  }

  return (
    <>
      <p style={{ color: "#888", fontSize: 13 }}>
        实时 · LiveEngine {LIVE_W}×{LIVE_H} · seed {LIVE_SEED} · 离线判读(不调 LLM)
      </p>

      <div ref={canvasWrapRef} onClick={handleClick} style={{ cursor: "crosshair" }}>
        <CanvasField frame={frame} />
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12 }}>
        <button
          data-testid="ca-live-play"
          onClick={() => setPlaying((p) => !p)}
        >
          {playing ? "暂停" : "播放"}
        </button>
        <button data-testid="ca-live-step" onClick={() => {
          const eng = engineRef.current;
          if (!eng) return;
          eng.step();
          setFrame(eng.frame());
        }}>
          单步
        </button>
        <button data-testid="ca-live-reset" onClick={reset}>
          重置
        </button>
        <span data-testid="ca-live-step-label">step {frame.step}</span>
      </div>

      <MicroscopePanel record={selected} />
    </>
  );
}
