from dataclasses import dataclass


@dataclass
class GameConfig:
    pool: float = 100.0
    rounds: int = 8
    grab_grab_penalty: float = 0.1
    verifier_retries: int = 2
    # provider names resolve via sim.llm.providers.PROVIDERS ("anthropic"/"deepseek"/"bailian"/...)
    agent_provider: str = "anthropic"
    verifier_provider: str = "anthropic"
    agent_model: str = "claude-haiku-4-5-20251001"
    verifier_model: str = "claude-opus-4-8"

    @property
    def chunk(self) -> float:
        return self.pool / self.rounds
