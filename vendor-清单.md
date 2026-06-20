# vendor 清单(实体已删,指针留存)

> 2026-06-19:锁定 Veridia 后,把 985M 的 `vendor/`(9 个浅克隆参考仓)删除以省空间。
> 这份清单保留"找得回"的能力——记录每个仓的 **URL + 精确 commit SHA**,需要时可精确复原到当时那一版。
> Veridia 代码**零引用**这些仓(它们只是早期调研的参考),所以删除不影响任何代码或测试。

## 清单(克隆时均为 `main` 分支、`--depth 1` 浅克隆)

| 仓 | 用途 / 当时判定 | License | URL | Commit SHA |
|---|---|---|---|---|
| **dgm** | Darwin Gödel Machine;曾想复用其 LLM 层,实际自建未 import | Apache-2.0 | https://github.com/jennyzzt/dgm | `a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2` |
| **openevolve** | 进化外循环 + trace 写法参考;实际自建未 import | Apache-2.0 | https://github.com/algorithmicsuperintelligence/openevolve | `80945ed82886d5c4ff2f3d22436765d50cb61266` |
| **langgraph** | 多 agent 编排/checkpoint 参考(未采用) | MIT | https://github.com/langchain-ai/langgraph | `ce6c8b2410f9921d379c8fe8ea8087d1934c07a9` |
| **smolagents** | 轻量 agent loop 参考(未采用) | Apache-2.0 | https://github.com/huggingface/smolagents | `526069c1ead958b36d9fd09a6b1ef37f68ed6ade` |
| **SWE-agent** | ❌ 不匹配(代码修复 agent,非本游戏) | MIT | https://github.com/SWE-agent/SWE-agent | `abd7d69724d1413b30fea43d4724bb5b463906b4` |
| **SWE-bench** | ❌ 不匹配(代码评测集) | MIT | https://github.com/SWE-bench/SWE-bench | `f7bbbb2ccdf479001d6467c9e34af59e44a840f9` |
| **SWE-ReX** | ❌ 不匹配(代码执行沙箱,本游戏不执行代码) | MIT | https://github.com/SWE-agent/SWE-ReX | `5c995c365dfb1fd5bc56fda688be5d8538f9931f` |
| **agentops** | observability,仅 UI/API 参考 | MIT | https://github.com/AgentOps-AI/agentops | `a855a92dfaa7fd4423f9a68b1ba0295a3a72da80` |
| **helicone** | observability SaaS,仅 UI/API 参考 | Apache-2.0 | https://github.com/Helicone/helicone | `4df16a30ab79bc6f31e4b3a29aca179d767db878` |

## 需要复原某个仓时(精确到当时那一版)

```bash
# 通用配方:克隆后 checkout 到记录的 SHA
git clone <URL> <dir> && git -C <dir> checkout <SHA>

# 例:复原 dgm 到当时的版本
git clone https://github.com/jennyzzt/dgm vendor/dgm \
  && git -C vendor/dgm checkout a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2
```

> 注:这些是活跃仓库,`main` 已继续前进;上面的 SHA 锁定的是 2026-06-19 调研时的快照。
