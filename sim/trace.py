import json


class TraceWriter:
    def __init__(self, game_id: str, config: dict) -> None:
        self._trace = {
            "game_id": game_id,
            "codename": "veridia",
            "config": config,
            "rounds": [],
            "winner": None,
            "metrics": {},
        }

    def add_round(self, round_dict: dict) -> None:
        self._trace["rounds"].append(round_dict)

    def finalize(self, winner: str, metrics: dict) -> None:
        self._trace["winner"] = winner
        self._trace["metrics"] = metrics

    def as_dict(self) -> dict:
        return self._trace

    def write(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._trace, f, ensure_ascii=False, indent=2)
