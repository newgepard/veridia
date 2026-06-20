# `llm/` — 共享 LLM 层

> Provider 抽象层。游戏/引擎逻辑只看见 `LLMClient` 协议，不关心背后是哪家模型。
> v0.2 的实时显微镜（`ca/run.py --live`）复用这一层；测试注入 `FakeLLM`，无需 API key。

## 文件地图

| 文件 | 职责 |
|---|---|
| `base.py` | `LLMClient` 协议 + `FakeLLM`（确定性假实现，供单测注入）。 |
| `providers.py` | `make_client(provider)` 工厂 + `PROVIDERS` 注册表（默认 DeepSeek）。 |
| `anthropic.py` | `AnthropicClient`（Anthropic SDK）。 |
| `openai_compatible.py` | `OpenAICompatibleClient`（DeepSeek / OpenAI 兼容端点）。 |

## 谁在用

- `ca/run.py --live` → `from llm.providers import make_client`
- 测试 `tests/test_llm.py`、`test_providers.py`、`test_ca_microscope.py`（注入 `FakeLLM`）

> 历史：本层原在 `sim/llm/`，v0.1 模拟删除后迁到根目录独立成模块。
