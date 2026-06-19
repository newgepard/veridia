import sys
from sim.config import GameConfig
from sim.engine import Engine
from sim.protocol import Message, MessageBus
from sim.memory import InMemoryStore
from sim.metrics import TrustTracker, count_lies, count_detected
from sim.verifier import Verifier
from sim.agents import VeridiaAgent, UmbraAgent
from sim.trace import TraceWriter


def promise_to_share(messages: list[Message], agent_id: str) -> bool:
    return any(m.from_ == agent_id and m.channel == "public" and "share" in m.text.lower()
               for m in messages)


def run_game(config: GameConfig, veridia_llm, umbra_llm, verifier_llm) -> dict:
    bus = MessageBus()
    mem = InMemoryStore()
    engine = Engine(config)
    trust = TrustTracker()
    verifier = Verifier(verifier_llm, config.verifier_model)
    umbra = UmbraAgent(umbra_llm, config.agent_model)
    veridia = VeridiaAgent(veridia_llm, config.agent_model, verifier, config.verifier_retries)
    tw = TraceWriter("veridia-local", {"pool": config.pool, "rounds": config.rounds,
                                       "verifier_retries": config.verifier_retries})

    for n in range(1, config.rounds + 1):
        u_turn = umbra.act(n, bus.visible_to("umbra"), mem.recall("umbra"))
        v_turn = veridia.act(n, bus.visible_to("veridia"), mem.recall("veridia"))
        round_msgs = u_turn.messages + v_turn.messages
        for m in round_msgs:
            bus.post(m)

        flags: list[str] = []
        if not v_turn.messages:
            flags.append("forced_silence")
        umbra_promised = promise_to_share(u_turn.messages, "umbra")
        umbra_kept = (umbra_promised and u_turn.action == "share")
        if umbra_promised and not umbra_kept:
            flags.append("umbra_broke_promise")
        trust.update("veridia_to_umbra", promise_kept=umbra_kept)

        pv, pu = engine.apply_round(v_turn.action, u_turn.action)
        round_dict = {
            "round": n,
            "private": {"veridia_state": v_turn.private_state,
                        "umbra_state": u_turn.private_state},
            "messages": [m.to_dict() for m in round_msgs],
            "actions": {"veridia": v_turn.action, "umbra": u_turn.action},
            "payoff": {"veridia": pv, "umbra": pu},
            "trust": trust.snapshot(),
            "scores": dict(engine.scores),
            "flags": flags,
        }
        tw.add_round(round_dict)
        mem.record("veridia", n, {"umbra_action": u_turn.action})
        mem.record("umbra", n, {"veridia_action": v_turn.action})

    rounds = tw.as_dict()["rounds"]
    tw.finalize(engine.winner(), {
        "lie_count": count_lies(rounds),
        "lies_detected": count_detected(rounds),
        "final_scores": dict(engine.scores),
    })
    return tw.as_dict()


def main() -> None:  # pragma: no cover (live; confirm IDs via claude-api skill)
    from sim.llm.providers import make_client
    cfg = GameConfig()
    # both civilizations use agent_provider; the judge uses verifier_provider.
    # cross-provider matchups = give each civ its own provider field later (1-line change).
    agent_client = make_client(cfg.agent_provider)
    verifier_client = make_client(cfg.verifier_provider)
    trace = run_game(cfg, agent_client, agent_client, verifier_client)
    import json, os
    os.makedirs("traces", exist_ok=True)
    path = f"traces/{trace['game_id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(trace, f, ensure_ascii=False, indent=2)
    print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
