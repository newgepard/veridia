import os


class AnthropicClient:
    def __init__(self, api_key: str | None = None) -> None:
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    def complete(self, system: str, user: str, model: str,
                 max_tokens: int = 1024) -> str:
        resp = self._client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text
