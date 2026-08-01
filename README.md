# FitCrew / BodyOS V2 Owner Alpha

## 中文

FitCrew 是产品与社区品牌，BodyOS 是用户在飞书中接触的私人健康教练，Moticlaw 是 Agent 的配置与管理入口。V2 Owner Alpha 把 Apple 健康、Apple 健身与鱼跃 Anytime 5 Pro 写入 Apple 健康的数据，经可选的 iOS HealthKit Bridge 接入本人专属服务。

当前版本只供 Owner 本人使用。飞书账号是主账号，内部用不可变的 `fitcrew_user_id` 绑定身份；Apple 设备和健康授权均为可选项。原始健康数据以 AES-GCM 加密保存，模型只接收确定性聚合特征、意图和带页码的私人知识摘录，不接收姓名、飞书 ID、聊天原文或原始健康序列。

群聊只允许五种固定低敏行为结果：完成今日行动、需要搭子、愿意分享、把行动变小、转到私聊获取个性化建议。个性化健康信息只在本人私聊出现，BodyOS 不做医疗诊断。

### 组件

- `apps/api/`：FastAPI、授权、加密摄取、日特征、知识/需求池与 BodyOS 模型边界。
- `apps/ios-bridge/`：HealthKit 最小读取授权、增量同步及第 16 天全量对账。
- `integrations/hermes/`：Moticlaw/Hermes 通道的预模型 Guard；Codex CLI 为主路由，Hermes OpenAI Codex OAuth 为备用。
- `infra/tencent/`：现有腾讯云东京 Lighthouse 的零新增现金部署、IP HTTPS、加密备份与 SHA 回滚。
- `scripts/import_private_books.py`：在 Git 外把本人提供的 PDF 加密导入私人知识库。

### 本地验证

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check apps/api scripts infra/tencent
(cd apps/ios-bridge/Core && swift test)
```

生产部署和物理设备步骤见 `docs/operations/deployment-and-rollback.md` 与 `docs/experiments/owner-cgm-16-day-runbook.md`。三本私人 PDF、健康导出、OAuth 凭据、飞书密钥、运行环境文件与真实证据均不得进入 Git。

产品介绍页保持在 <https://flicy.github.io/cola-pages/fitcrew/>。本仓库所有变更通过 PR 进入 `main`；未经 Owner 明确批准不合并或发布版本。

## English

FitCrew is the product and community brand, BodyOS is the private health coach users meet in Feishu, and Moticlaw is the Agent configuration and management surface. V2 Owner Alpha connects Apple Health, Apple Fitness, and Yuwell Anytime 5 Pro data written into Apple Health through an optional iOS HealthKit Bridge to an owner-dedicated service.

This release is owner-only. Feishu is the primary account while an immutable internal `fitcrew_user_id` binds identities; Apple devices and health authorization are optional. Raw health fields are encrypted with AES-GCM. A model receives only deterministic aggregates, intent, and page-cited private knowledge excerpts—never names, Feishu IDs, raw chat, or raw health series.

Group chat permits only five fixed low-sensitivity outcomes: today's action completed, need a buddy, willing to share, make the action smaller, or move to DM for personalized guidance. Personalized health information stays in the owner's DM, and BodyOS does not diagnose.

### Components

- `apps/api/`: FastAPI, consent, encrypted ingestion, daily features, knowledge/demand pools, and the BodyOS model boundary.
- `apps/ios-bridge/`: minimum HealthKit read authorization, incremental sync, and day-16 reconciliation.
- `integrations/hermes/`: the pre-model guard for Moticlaw/Hermes channels; Codex CLI is primary and Hermes OpenAI Codex OAuth is fallback.
- `infra/tencent/`: zero-new-cash deployment, IP HTTPS, encrypted backups, and SHA rollback on the existing Tokyo Lighthouse.
- `scripts/import_private_books.py`: encrypted private-book import outside Git.

### Local verification

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check apps/api scripts infra/tencent
(cd apps/ios-bridge/Core && swift test)
```

See `docs/operations/deployment-and-rollback.md` and `docs/experiments/owner-cgm-16-day-runbook.md` for production and physical-device steps. Private PDFs, health exports, OAuth credentials, Feishu secrets, runtime environments, and real private evidence must never enter Git.

The product page remains at <https://flicy.github.io/cola-pages/fitcrew/>. All repository changes reach `main` through a PR; no merge or release occurs without explicit owner approval.
