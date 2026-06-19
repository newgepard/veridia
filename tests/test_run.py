import json
from sim.config import GameConfig
from sim.run import run_game, promise_to_share
from sim.protocol import Message
from sim.llm.base import FakeLLM


def test_promise_to_share_detects_public_share():
    msgs = [Message("umbra", "veridia", "public", "I promise I will SHARE")]
    assert promise_to_share(msgs, "umbra") is True
    assert promise_to_share([Message("umbra", "veridia", "dm", "share")], "umbra") is False


def test_run_game_2_rounds_deterministic():
    cfg = GameConfig(pool=100.0, rounds=2)

    def turn(action, text, private):
        return json.dumps({"private_state": private,
                           "messages": [{"to": "umbra", "channel": "public", "text": text}],
                           "action": action})

    # Umbra promises share but grabs both rounds (broken promises)
    umbra = FakeLLM([
        json.dumps({"private_state": {"intent": "grab"},
                    "messages": [{"to": "veridia", "channel": "public", "text": "I will share"}],
                    "action": "grab"}),
        json.dumps({"private_state": {"intent": "grab"},
                    "messages": [{"to": "veridia", "channel": "public", "text": "share again"}],
                    "action": "grab"}),
    ])
    veridia = FakeLLM([
        turn("share", "I will share", {"intent": "share", "true_pool": 100}),
        turn("grab", "I will grab now", {"intent": "grab", "true_pool": 50}),
    ])
    verifier = FakeLLM(['{"verdict": "truthful", "reason": "ok"}'] * 2)

    trace = run_game(cfg, veridia, umbra, verifier)
    assert len(trace["rounds"]) == 2
    r0 = trace["rounds"][0]
    assert set(r0) >= {"round", "private", "messages", "actions", "payoff",
                       "trust", "scores", "flags"}
    assert "umbra_broke_promise" in r0["flags"]            # promised share, grabbed
    assert trace["winner"] in ("veridia", "umbra", "tie")
    assert trace["metrics"]["lie_count"] >= 1
