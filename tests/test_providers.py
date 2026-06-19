import pytest
from sim.llm.providers import PROVIDERS, make_client
from sim.llm.openai_compatible import OpenAICompatibleClient
from sim.llm.anthropic import AnthropicClient


def test_registry_has_wired_providers():
    assert PROVIDERS["deepseek"]["base_url"] == "https://api.deepseek.com"
    assert PROVIDERS["deepseek"]["default_model"] == "deepseek-chat"
    assert PROVIDERS["bailian"]["base_url"].endswith("/compatible-mode/v1")
    assert PROVIDERS["bailian"]["default_model"] == "qwen-plus"
    assert PROVIDERS["anthropic"]["kind"] == "anthropic"


def test_unknown_provider_raises():
    with pytest.raises(KeyError):
        make_client("nope")


def test_make_client_builds_offline_with_explicit_key():
    # explicit api_key avoids env + avoids any network call (SDKs construct lazily)
    assert isinstance(make_client("deepseek", api_key="dummy"), OpenAICompatibleClient)
    assert isinstance(make_client("bailian", api_key="dummy"), OpenAICompatibleClient)
    assert isinstance(make_client("anthropic", api_key="dummy"), AnthropicClient)
