from dataclasses import dataclass


@dataclass
class GameConfig:
    pool: float = 100.0
    rounds: int = 8
    grab_grab_penalty: float = 0.1
    verifier_retries: int = 2
    # provider names resolve via sim.llm.providers.PROVIDERS ("anthropic"/"deepseek"/"bailian"/...)
    # Clean benchmark baseline: SAME model on both civilizations + judge, so the only variable
    # is the honesty/transparency constraint (not a model-capability confound). Cross-provider
    # matchups are a SEPARATE experiment — opt in by changing these, don't mix into the baseline.
    agent_provider: str = "deepseek"
    verifier_provider: str = "deepseek"
    agent_model: str = "deepseek-chat"      # V3 (latest)
    verifier_model: str = "deepseek-chat"   # judge; swap to "deepseek-reasoner" (R1) only if you
                                            # accept a small judge-vs-player asymmetry

    @property
    def chunk(self) -> float:
        return self.pool / self.rounds
