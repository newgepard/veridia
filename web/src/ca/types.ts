// 帧状态契约的 TS 镜像(对应 ca/state.py)。前端只认这个形状,与具体 CA 规则无关。

export const HONEST = 0;
export const MANIPULATIVE = 1;

export interface Frame {
  step: number;
  width: number;
  height: number;
  belief: number[]; // H*W 行优先, [0,1] —— 渲染主通道(Lenia 场)
  type: number[]; // H*W, 0=honest 1=manipulative
  standing: number[]; // H*W, [0,1]
}

export interface MicroscopeRecord {
  step: number;
  x: number;
  y: number;
  claim: string;
  verdict: string; // "truthful" | "lie"
  reason: string;
}

export interface CATrace {
  game_id: string;
  codename: string; // "veridia-ca"
  config: Record<string, unknown>;
  frames: Frame[];
  microscope: MicroscopeRecord[];
}
