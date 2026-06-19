import json
from sim.agents import UmbraAgent, VeridiaAgent, AgentTurn, _parse_turn
from sim.verifier import Verifier
from sim.llm.base import FakeLLM


def _turn_json(action, msgs, private):
    return json.dumps({"private_state": private, "messages": msgs, "action": action})


def test_parse_turn():
    raw = 'ok ' + _turn_json("grab", [{"to": "veridia", "channel": "dm", "text": "trust me"}],
                             {"intent": "grab"})
    d = _parse_turn(raw)
    assert d["action"] == "grab"
    assert d["messages"][0]["channel"] == "dm"


def test_umbra_posts_messages_verbatim():
    llm = FakeLLM([_turn_json("grab",
                              [{"to": "veridia", "channel": "public", "text": "I'll share!"}],
                              {"intent": "grab"})])
    turn = UmbraAgent(llm, "m").act(1, [], [])
    assert turn.action == "grab"
    assert turn.messages[0].verdict is None
    assert turn.messages[0].from_ == "umbra"


def test_veridia_truthful_message_kept():
    agent_llm = FakeLLM([_turn_json("share",
                                    [{"to": "umbra", "channel": "public", "text": "I will share"}],
                                    {"intent": "share", "true_pool": 100})])
    verifier = Verifier(FakeLLM(['{"verdict": "truthful", "reason": "ok"}']), "vm")
    turn = VeridiaAgent(agent_llm, "m", verifier, retries=2).act(1, [], [])
    assert turn.messages[0].channel == "public"
    assert turn.messages[0].verdict == "truthful"


def test_veridia_lie_is_redrafted():
    # first turn proposes a lie; redraft prompt returns a single truthful message
    agent_llm = FakeLLM([
        _turn_json("grab",
                   [{"to": "umbra", "channel": "public", "text": "I will share"}],
                   {"intent": "grab", "true_pool": 100}),
        json.dumps({"text": "I have not decided yet"}),  # redraft response
    ])
    verifier = Verifier(FakeLLM([
        '{"verdict": "lie", "reason": "intent is grab"}',
        '{"verdict": "truthful", "reason": "vague, not a lie"}',
    ]), "vm")
    turn = VeridiaAgent(agent_llm, "m", verifier, retries=2).act(1, [], [])
    assert turn.action == "grab"
    assert turn.messages[0].text == "I have not decided yet"
    assert turn.messages[0].verdict == "truthful"


def test_veridia_forced_silence_after_exhausting_retries():
    agent_llm = FakeLLM([
        _turn_json("grab",
                   [{"to": "umbra", "channel": "public", "text": "I will share"}],
                   {"intent": "grab"}),
        json.dumps({"text": "still lying, I will share"}),
    ])
    verifier = Verifier(FakeLLM([
        '{"verdict": "lie", "reason": "x"}',
        '{"verdict": "lie", "reason": "x"}',
    ]), "vm")
    turn = VeridiaAgent(agent_llm, "m", verifier, retries=1).act(1, [], [])
    assert turn.messages == []  # dropped; orchestrator records forced_silence
