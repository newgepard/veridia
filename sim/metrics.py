class TrustTracker:
    def __init__(self, initial: float = 0.5) -> None:
        self.trust = {"veridia_to_umbra": initial, "umbra_to_veridia": initial}

    def update(self, key: str, promise_kept: bool, step: float = 0.2) -> None:
        delta = step if promise_kept else -step
        self.trust[key] = max(0.0, min(1.0, self.trust[key] + delta))

    def snapshot(self) -> dict:
        return {k: round(v, 4) for k, v in self.trust.items()}


def count_lies(rounds: list[dict]) -> int:
    return sum(1 for r in rounds if "umbra_broke_promise" in r.get("flags", []))


def count_detected(rounds: list[dict]) -> int:
    return sum(1 for r in rounds
               if "umbra_broke_promise" in r.get("flags", [])
               and r.get("trust", {}).get("veridia_to_umbra", 1.0) < 0.5)
