# Veridia v0.2 — 会自己长出真话与谎言的宇宙

> 一句话：**一个会自己长出真话与谎言的宇宙——远看是涌现的生物在格子上厮杀，点开任意一只，LLM 宪法法院把它读成一个谎。**
>
> 两类细胞在格子上博弈：**晶族（honest，水晶的晶）只说自己相信为真的话；雾族（manipulative，起雾的雾）说与所知相反的话。** 单一法则 F 在创世时立下、之后神缺席——生命自机械法则中涌现。

---

## 模块地图（按功能划分）

| 模块 | 职责 | 模块文档 |
|---|---|---|
| `ca/` | **后端核心**：v0.2 复杂科学 CA（Lenia 引擎 / 转移规则 / 引擎 / LLM 显微镜 / 帧契约） | [`ca/README.md`](ca/README.md) |
| `llm/` | **共享 LLM 层**：provider 抽象（DeepSeek/Anthropic/OpenAI 兼容）+ `FakeLLM`，被 `ca/` 实时显微镜复用 | [`llm/README.md`](llm/README.md) |
| `web/` | **前端**：Vite+React+TS + canvas 2D，回放/实时两种模式 | [`web/frontend.md`](web/frontend.md) |
| `tests/` | Python 测试（pytest，注入 `FakeLLM`，无需 API key） | — |
| `docs/v0.2-viz/` | 可视化截图素材 | — |

> 文档约定：**项目级文档放根目录；模块文档放各自模块文件夹**。

## 项目级文档

- [72h 作战图](veridia-v0.2-黑客松-72h作战图.md) — 方案锁定、不变量、三线并行计划
- [三线集成 & Handoff](handoff-三线集成.md) — 视频 / 前端 / 后端 的交接与集成节点
- [前后端契约](frontend-backend-契约.md) — 帧状态契约（集成面，唯一耦合点）
- [Backlog](veridia-v0.2-backlog.md) — 字段回补清单（按 ROI）
- [vendor 清单](vendor-清单.md) — 已删参考仓的 SHA 指针

## 怎么跑

**后端（Python ≥ 3.11）**
```bash
source .venv/bin/activate
python -m pytest -q          # 全部测试
python -m ca.run             # 离线生成喂前端的 trace（零 LLM，无需 key）
python -m ca.run --live      # 真 LLM 显微镜判读（需 DEEPSEEK_API_KEY）
```

**前端**
```bash
cd web
npm install
npm run dev                  # 本地预览
npm run test                 # vitest
```

## 不变量（不可动摇）

- **litmus**：关掉 LLM，CA 必须能跑到底（LLM 只在显微镜环节出现，read-only，绝不写回 belief/type/standing）。
- **trace 驱动**：一切可视化 = 帧状态（Frame）的纯函数；前后端只经帧状态契约耦合。
- **句法/语义分层**：CA=句法（机械涌现）；LLM=语义（立法 F + 显微镜判读）。
