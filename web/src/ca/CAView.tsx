import { type CSSProperties, useEffect, useMemo, useRef, useState } from "react";
import type { CATrace, Frame, MicroscopeRecord } from "./types";
import { MANIPULATIVE } from "./types";
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
const MIN_ZOOM = 0.85;
const MAX_ZOOM = 3;

interface FrameStats {
  active: number;
  truthPct: number;
  liePct: number;
}

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

function frameStats(frame: Frame): FrameStats {
  let active = 0;
  let truth = 0;
  let lie = 0;
  for (let i = 0; i < frame.width * frame.height; i++) {
    if ((frame.belief[i] ?? 0) < 0.05) continue;
    active++;
    if ((frame.type[i] ?? 0) === MANIPULATIVE) lie++;
    else truth++;
  }
  const total = active || 1;
  return {
    active,
    truthPct: Math.round((truth / total) * 100),
    liePct: Math.round((lie / total) * 100),
  };
}

function clampZoom(value: number): number {
  return Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, value));
}

function zoomStyle(zoom: number): CSSProperties {
  return { "--ca-zoom": String(zoom) } as CSSProperties;
}

function useWheelZoom() {
  const [zoom, setZoom] = useState(1);
  function handleWheel(e: React.WheelEvent<HTMLDivElement>) {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
    setZoom((current) => Math.round(clampZoom(current * factor) * 100) / 100);
  }
  return { zoom, handleWheel };
}

function CanvasReadout({ frame, zoom }: { frame: Frame; zoom: number }) {
  const stats = useMemo(() => frameStats(frame), [frame]);
  return (
    <div className="ca-readout" aria-label="cell field readout">
      <span className="ca-readout-truth">TRUTH {String(stats.truthPct).padStart(2, "0")}%</span>
      <span className="ca-readout-lie">LIE {String(stats.liePct).padStart(2, "0")}%</span>
      <span>CELLS {String(stats.active).padStart(4, "0")}</span>
      <span>ZOOM {zoom.toFixed(2)}x</span>
    </div>
  );
}

export function CAView() {
  const [mode, setMode] = useState<"replay" | "live">("replay");
  return (
    <section data-testid="ca-view" className="ca-view">
      <div className="ca-vignette" aria-hidden="true" />
      <header className="ca-topbar">
        <div className="ca-brand">
          <h1 data-testid="ca-shell-title">VERIDIA</h1>
          <p>one law, spoken, withdrawn</p>
        </div>
        <div className="ca-mode-switch" aria-label="simulation mode">
          <button
            data-testid="ca-mode-replay"
            className={mode === "replay" ? "is-active" : ""}
            onClick={() => setMode("replay")}
          >
            REPLAY
          </button>
          <button
            data-testid="ca-mode-live"
            className={mode === "live" ? "is-active" : ""}
            onClick={() => setMode("live")}
          >
            LIVE
          </button>
        </div>
      </header>
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
  const { zoom, handleWheel } = useWheelZoom();

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
    <div className="ca-experience">
      <div className="ca-statusline">
        <span>ARCHIVE {trace.game_id}</span>
        <span>{frames.length} FRAMES</span>
        <span>{verdictCount} COURT RECORDS</span>
      </div>

      <div
        ref={canvasWrapRef}
        onClick={handleClick}
        onWheel={handleWheel}
        className="ca-canvas-stage"
        style={zoomStyle(zoom)}
      >
        <CanvasField frame={frame} />
      </div>

      <CanvasReadout frame={frame} zoom={zoom} />

      <div className="ca-controls">
        <button
          className="ca-control"
          data-testid="ca-play"
          onClick={() => {
            if (step >= maxStep) setStep(0);
            setPlaying((p) => !p);
          }}
        >
          {playing ? "PAUSE" : "PLAY"}
        </button>
        <input
          className="ca-range"
          type="range"
          data-testid="ca-step"
          aria-label="replay step"
          min={0}
          max={maxStep}
          value={step}
          onChange={(e) => {
            setPlaying(false);
            setStep(Number(e.target.value));
          }}
        />
        <span className="ca-step-label" data-testid="ca-step-label">
          step {frame.step} / {maxStep}
        </span>
      </div>

      <MicroscopePanel record={selected} />
    </div>
  );
}

// 实时模式:浏览器里跑 LiveEngine,setInterval 不断 step+重渲。
// 点击 → 确定性离线判读模板(不调 LLM)。
function LiveView() {
  const engineRef = useRef<LiveEngine | null>(null);
  if (engineRef.current === null) {
    engineRef.current = new LiveEngine(LIVE_W, LIVE_H, LIVE_SEED);
  }
  const [frame, setFrame] = useState<Frame>(() => engineRef.current!.frame());
  const [playing, setPlaying] = useState(false);
  const [selected, setSelected] = useState<MicroscopeRecord | null>(null);
  const { zoom, handleWheel } = useWheelZoom();

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
    <div className="ca-experience">
      <div className="ca-statusline">
        <span>LIVEENGINE {LIVE_W}x{LIVE_H}</span>
        <span>SEED {LIVE_SEED}</span>
        <span>OFFLINE COURT</span>
      </div>

      <div
        ref={canvasWrapRef}
        onClick={handleClick}
        onWheel={handleWheel}
        className="ca-canvas-stage"
        style={zoomStyle(zoom)}
      >
        <CanvasField frame={frame} />
      </div>

      <CanvasReadout frame={frame} zoom={zoom} />

      <div className="ca-controls">
        <button
          className="ca-control"
          data-testid="ca-live-play"
          onClick={() => setPlaying((p) => !p)}
        >
          {playing ? "PAUSE" : "PLAY"}
        </button>
        <button
          className="ca-control"
          data-testid="ca-live-step"
          onClick={() => {
            const eng = engineRef.current;
            if (!eng) return;
            eng.step();
            setFrame(eng.frame());
          }}
        >
          STEP
        </button>
        <button className="ca-control" data-testid="ca-live-reset" onClick={reset}>
          RESET
        </button>
        <span className="ca-step-label" data-testid="ca-live-step-label">
          step {frame.step}
        </span>
      </div>

      <MicroscopePanel record={selected} />
    </div>
  );
}
