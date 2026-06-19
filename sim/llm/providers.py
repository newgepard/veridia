"""Provider registry. Adding a new OpenAI-compatible provider = ONE row here.
Game logic (engine/agents/verifier/...) never imports this — it only sees LLMClient."""
from sim.llm.anthropic import AnthropicClient
from sim.llm.openai_compatible import OpenAICompatibleClient

# name -> spec. kind "anthropic" uses native messages API; "openai" uses chat.completions.
PROVIDERS: dict[str, dict] = {
    "anthropic": {
        "kind": "anthropic",
        "api_key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-opus-4-8",
    },
    "deepseek": {
        "kind": "openai",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",  # V3 (latest); reasoner = "deepseek-reasoner" (R1)
    },
    "bailian": {  # 阿里百炼 / DashScope OpenAI-compatible mode
        "kind": "openai",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "default_model": "qwen-plus",  # also qwen-max / qwen-turbo / qwen3-*
    },
    # --- To add more, copy one row (no code changes anywhere else): ---
    # "openrouter": {"kind": "openai", "base_url": "https://openrouter.ai/api/v1",
    #                "api_key_env": "OPENROUTER_API_KEY", "default_model": "..."},
    # "ollama":     {"kind": "openai", "base_url": "http://localhost:11434/v1",
    #                "api_key_env": None, "default_model": "qwen2.5"},
    # "kimi":       {"kind": "openai", "base_url": "https://api.moonshot.cn/v1",
    #                "api_key_env": "MOONSHOT_API_KEY", "default_model": "kimi-k2"},
}


def make_client(provider: str, api_key: str | None = None):
    """Build an LLMClient for the named provider. Raises KeyError on unknown provider."""
    spec = PROVIDERS[provider]
    if spec["kind"] == "anthropic":
        return AnthropicClient(api_key=api_key)
    return OpenAICompatibleClient(
        base_url=spec["base_url"],
        api_key=api_key,
        api_key_env=spec.get("api_key_env"),
    )
