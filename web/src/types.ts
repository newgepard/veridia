export type Action = "share" | "grab";
export type Channel = "public" | "dm";
export type Verdict = "truthful" | "lie" | null;

export interface TraceMessage {
  from: string;
  to: string;
  channel: Channel;
  text: string;
  verdict: Verdict;
}

export interface Round {
  round: number;
  private: { veridia_state: Record<string, unknown>; umbra_state: Record<string, unknown> };
  messages: TraceMessage[];
  actions: { veridia: Action; umbra: Action };
  payoff: { veridia: number; umbra: number };
  trust: { veridia_to_umbra: number; umbra_to_veridia: number };
  scores: { veridia: number; umbra: number };
  flags: string[];
}

export interface Trace {
  game_id: string;
  codename: string;
  config: Record<string, unknown>;
  rounds: Round[];
  winner: string;
  metrics: { lie_count: number; lies_detected: number; final_scores: Record<string, number> };
}
