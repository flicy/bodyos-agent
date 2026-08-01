# Owner Alpha Verification / Owner Alpha 验证

## 中文

### PR 范围

分支 `codex/v2-owner-alpha` 基于 `main` 的 `c5263b3`，实现 Owner-only FitCrew/BodyOS V2 Alpha。未经 Owner 批准，本 PR 不合并、不创建 Release。

### 已验证

- Python：78 项测试通过；包含身份/授权、AES-GCM、幂等摄取、日聚合、DLP、群策略、模型 envelope、知识版本、需求状态、保留和运维检查。
- Swift Core：10 项测试通过；包含契约、单位、批次、游标、配对与第 16 天一次性全量对账。
- Codex CLI 主路由真实 OAuth canary 返回预期；Hermes `openai-codex` 备用真实 OAuth canary 返回预期。备用 HTTP 错误不再被误判为成功。
- 三份本人 PDF 仅在 Git 外验收：页数 252/6/20，可提取文字页 247/6/19；隔离库导入 3 个来源、367 个 AES-GCM 分段，三类检索命中，重复导入后来源数仍为 3。内容与完整哈希不进入本文件。
- 本地 ruff、Bash、JSON、YAML、双语 Markdown 与秘密扫描通过；工作树在提交时干净。

### CI 与上线门禁

GitHub CI 必须继续证明 Linux Docker 镜像、Compose 迁移/健康检查和完整 iOS Simulator 编译。腾讯云上线必须记录实际部署 SHA、HTTPS、服务重启、模型登录、定时器、加密备份、恢复演练和回滚健康门禁。

真实数据只在 Owner iPhone 完成 HealthKit 权限与扫描一次性配对 QR 后验证；证据只保留样本计数、来源/时间窗、时区/单位质量和同步状态，不记录数值。第 16 天结论必须等待真实时间，不会在启动日提前声称完成。

### 回滚

应用回滚目标是上一份已经构建并验证的 40 位镜像 SHA；数据库变更不自动降级。若迁移不向后兼容，先停止写入并恢复经过 `restore-test.sh` 验证的加密备份。V1 脏工作树和现有官网不得被覆盖。

## English

### PR scope

Branch `codex/v2-owner-alpha` starts from `main` at `c5263b3` and implements the owner-only FitCrew/BodyOS V2 Alpha. The PR is not merged and no Release is created without owner approval.

### Verified

- Python: 78 tests pass, covering identity/consent, AES-GCM, idempotent ingestion, daily aggregates, DLP, group policy, model envelopes, knowledge versioning, demand state, retention, and operations.
- Swift Core: 10 tests pass, covering the contract, units, batches, cursor, pairing, and one-time day-16 reconciliation.
- A real OAuth Codex CLI primary canary returned the expected result; a real Hermes `openai-codex` fallback canary returned the expected result. Fallback HTTP errors can no longer be mistaken for success.
- Three owner PDFs were verified outside Git only: 252/6/20 pages with 247/6/19 text-bearing pages. An isolated database imported three sources and 367 AES-GCM chunks; all three retrieval checks passed and replay left the source count at three. Content and complete hashes are omitted here.
- Local ruff, Bash, JSON, YAML, bilingual-Markdown, and secret checks pass; the worktree was clean at commit time.

### CI and production gates

GitHub CI must still prove the Linux Docker image, Compose migration/health smoke test, and complete iOS Simulator build. Tencent production evidence must record the actual deploy SHA, HTTPS, service restart, model login, timers, encrypted backup, restore drill, and rollback health gate.

Real data is verified only after the owner authorizes HealthKit on the iPhone and scans the one-time pairing QR. Evidence retains only sample counts, source/window, timezone/unit quality, and sync status—never values. The day-16 conclusion waits for real elapsed time and is never claimed on the start day.

### Rollback

Application rollback targets the previous built and verified 40-character image SHA; database migrations are not auto-downgraded. For an incompatible migration, stop writes and restore an encrypted backup already validated by `restore-test.sh`. The dirty V1 worktree and existing product site must not be overwritten.
