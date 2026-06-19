from dataclasses import dataclass, field
from sim.config import GameConfig


def resolve_round(action_v: str, action_u: str, chunk: float, penalty: float = 0.1):
    if action_v == "share" and action_u == "share":
        return (chunk / 2, chunk / 2)
    if action_v == "grab" and action_u == "share":
        return (chunk, 0.0)
    if action_v == "share" and action_u == "grab":
        return (0.0, chunk)
    return (chunk * penalty, chunk * penalty)  # both grab


@dataclass
class Engine:
    config: GameConfig
    scores: dict = field(default_factory=lambda: {"veridia": 0.0, "umbra": 0.0})

    def apply_round(self, action_v: str, action_u: str):
        pv, pu = resolve_round(action_v, action_u, self.config.chunk,
                               self.config.grab_grab_penalty)
        self.scores["veridia"] += pv
        self.scores["umbra"] += pu
        return pv, pu

    def winner(self) -> str:
        v, u = self.scores["veridia"], self.scores["umbra"]
        if v > u:
            return "veridia"
        if u > v:
            return "umbra"
        return "tie"
