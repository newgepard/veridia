import pytest
from sim.config import GameConfig
from sim.engine import resolve_round, Engine


def test_payoff_matrix():
    assert resolve_round("share", "share", 12.0) == (6.0, 6.0)
    assert resolve_round("grab", "share", 12.0) == (12.0, 0.0)
    assert resolve_round("share", "grab", 12.0) == (0.0, 12.0)
    assert resolve_round("grab", "grab", 12.0, penalty=0.1) == pytest.approx((1.2, 1.2))


def test_engine_accumulates_and_picks_winner():
    e = Engine(GameConfig(pool=100.0, rounds=8))
    e.apply_round("grab", "share")   # veridia +12.5
    e.apply_round("share", "share")  # +6.25 each
    assert e.scores["veridia"] == pytest.approx(18.75)
    assert e.scores["umbra"] == pytest.approx(6.25)
    assert e.winner() == "veridia"


def test_tie():
    e = Engine(GameConfig())
    assert e.winner() == "tie"
