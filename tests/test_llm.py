import pytest
from llm.base import FakeLLM


def test_fake_llm_pops_and_records():
    llm = FakeLLM(["first", "second"])
    assert llm.complete("sys", "u1", "m") == "first"
    assert llm.complete("sys", "u2", "m") == "second"
    assert llm.calls[0] == {"system": "sys", "user": "u1", "model": "m"}
    with pytest.raises(IndexError):
        llm.complete("sys", "u3", "m")
