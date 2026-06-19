from sim.config import GameConfig


def test_defaults_and_chunk():
    c = GameConfig()
    assert c.pool == 100.0
    assert c.rounds == 8
    assert c.grab_grab_penalty == 0.1
    assert c.verifier_retries == 2
    assert c.chunk == 12.5
    assert c.agent_model and c.verifier_model
