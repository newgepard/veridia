import os


class OpenAICompatibleClient:
    """One client for every OpenAI-compatible provider (DeepSeek, 阿里百炼/DashScope,
    OpenRouter, Ollama, Kimi, GLM, ...). Only base_url + key differ — see providers.py."""

    def __init__(self, base_url: str, api_key: str | None = None,
                 api_key_env: str | None = None) -> None:
        from openai import OpenAI
        key = api_key or (os.environ[api_key_env] if api_key_env else None) or "not-needed"
        self._client = OpenAI(base_url=base_url, api_key=key)

    def complete(self, system: str, user: str, model: str,
                 max_tokens: int = 1024) -> str:
        resp = self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content
