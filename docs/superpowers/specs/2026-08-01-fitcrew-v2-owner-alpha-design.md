# FitCrew / BodyOS V2 Owner-only Alpha Design

> Status: approved product boundary, 2026-08-01  
> 状态：已确认产品边界，2026-08-01

## 中文版

### 1. 目标

本版本把现有 FitCrew V1 Agent 安装包升级为一个可以实际运行的 Owner-only V2 Alpha。当天的软件交付必须覆盖 GitHub PR、腾讯云部署、BodyOS 飞书群聊与私聊、Apple Health/鱼跃数据通路、确定性健康特征、私人知识检索、授权与删除，以及 Motclaw 到 Codex Harness 的主模型链路和 Hermes 备用链路。

16 天实验的程序、监控和首次真实数据同步在当天启动；第 16 天的最终结果只能在真实时间经过后生成。

### 2. 名称和范围

- FitCrew 是产品与品牌。
- BodyOS 是 FitCrew 内面向用户的 AI 健康助手。
- Motclaw 是 Agent 运行时。
- Codex Harness 是主要模型能力，使用已有订阅 OAuth；Hermes 仅按需备用。
- 飞书账号是用户入口，`fitcrew_user_id` 是不可变的数据归属主键。
- Apple Health 是可选连接器，不是使用 FitCrew 的前置条件。

本 Alpha 只服务产品所有者的真实健康数据。5-20 人真实健康试点、TestFlight、WHOOP、企业微信、内容渠道、海外渠道、中国大陆生产环境和 ICP 不在本次实现范围。

### 3. 单机目标架构

现有腾讯云东京 Lighthouse 是唯一云资源。为了保持零新增现金和适配 2 核 4 GB，使用一个最小 Docker Compose 部署：

```text
iPhone HealthKit Bridge ----HTTPS----> API ----> PostgreSQL
                                          |          |
Feishu <---- BodyOS/Motclaw <---- scoped tools       |
                         |                |           |
                  Codex Harness      policy/DLP <-----+
                         |
                  Hermes on demand

PDF importer ----> encrypted private knowledge ----> retrieval
Feishu capture ---> candidate/demand pools ---------> review
```

API、Worker、PostgreSQL 和反向代理常驻；Hermes 不与 Motclaw长期双开。没有现成免费额度时，不创建 TencentDB、TKE、WAF、API Gateway、KMS、SSM、COS 或独立向量数据库。

### 4. 数据与权限

数据按用途而不是按文件名授权：

| 数据 | 私聊 | 群聊 | 模型 |
|---|---|---|---|
| 原始 CGM、睡眠、HRV、心率 | 经授权可查询摘要 | 永久禁止 | 禁止 |
| 确定性日级特征 | 经授权可解释 | 永久禁止 | 去标识化最小窗口 |
| 私人知识源 | 本人可检索 | 禁止 | 只发送命中的最小片段 |
| 行为令牌 | 可见 | 用户预览确认后可见 | 可用于措辞 |
| 公共已审核知识 | 可见 | 可见 | 可检索 |

群 scope 调用私人、健康或私人知识工具必须由程序返回 `403`。群消息只能由固定行为令牌生成，不能靠提示词避免泄露。

每次处理必须携带 `fitcrew_user_id`、`purpose`、`scope`、`data_categories`、`consent_id` 和保留策略。撤回立即停止采集、检索、模型处理和分享。

### 5. 健康数据

iOS Bridge 读取最小 HealthKit 集合：血糖、睡眠汇总、HRV、静息心率、锻炼、活动能量、步数、站立和活动圆环。鱼跃首选通过“安耐糖写 Apple Health”进入同一路径。

每条样本保留来源、设备、开始/结束时间、原始单位、规范单位、同步批次和 HealthKit UUID。批次采用幂等键，支持断网重试、每日增量同步和第 16 天全量回读。

原始值应用层加密；元数据只保留完成同步和授权所需字段。原始明细默认保留 30 天，授权后的日级汇总和洞察最长 13 个月。

确定性特征包括数据质量、日级血糖摘要、餐后窗口、夜间稳定性、睡眠、HRV、静息心率和运动活动汇总。模型永远不接收原始健康时间序列。

### 6. BodyOS 与模型

BodyOS 私聊提供同步状态、数据质量、带证据的私人洞察、知识问答、授权、撤回、导出和删除。

群聊仅允许 `completed`、`need_buddy`、`willing_to_share` 和 `smaller_action` 等固定令牌，并要求发送前确认。现有未授权全群读取和全员主动周报关闭。

模型主路径为 Motclaw 到 Codex Harness。超时、认证失败或额度耗尽时，先进入有限重试和熔断，再按需调用 Hermes；两个路径都不可用时失败关闭并保留任务，不能切换付费 API。

### 7. 知识与需求池

三本本地 PDF 是用户私人知识源，不进入 Git 或公共知识库。导入保存哈希、书目、页码、版本、版权状态和导入时间，正文分段后加密保存。检索结果必须引用书名和页码，并区分书中观点、一手证据、用户数据和模型推断。

公共知识采用 `captured -> deidentified -> under_review -> approved -> published`；需求采用 `new -> clustered -> validated -> planned/declined -> shipped -> measured`。BodyOS 只把已发布公共知识用于事实性回答。个人健康数据、成员身份和群聊原文永不进入公共知识库。

### 8. GitHub 和发布

`flicy/fitcrew-agent` 是主仓库，所有修改从 `codex/v2-owner-alpha` 经 PR 进入 `main`。CI 检查 Python、Swift、Shell、配置、测试和秘密。未经用户批准不合并。部署记录 PR SHA；用户批准合并后才创建 `v2.0.0-alpha.1` Release。

`flicy/cola-pages` 只保留官网发布职责，现有 URL 不能中断。

### 9. 安全和运维门槛

- 默认拒绝，最小端口和最小工具权限。
- 密钥不进 Git、日志或镜像，运行文件权限至少 `0600`。
- 日志不记录聊天正文、健康值、PDF 正文或身份映射。
- 备份、恢复和回滚必须真实执行。
- 跨群金丝雀、注入、错绑、撤回、DLP 和删除必须有自动化负向测试。
- 不删除或重置旧本地工作区和现有 V1 数据。
- 不向非测试群或其他成员发送测试消息。

### 10. 当天验收

当天软件完成要求：PR 和 CI、Owner-only 云部署、首批真实 HealthKit/鱼跃同步、BodyOS 私聊和群行为令牌、三本 PDF 私人检索、模型主备路径、导出/撤回/删除、安全测试和回滚证据均可验证。若真机授权或账号验证需要用户操作，必须报告唯一最小动作；不能以模拟数据冒充真实闭环。

## English Version

### 1. Objective

This release upgrades the existing FitCrew V1 Agent package into an operational owner-only V2 Alpha. The same-day software delivery covers GitHub PRs, Tencent Cloud deployment, BodyOS Feishu DM and group behavior, Apple Health and Yuwell ingestion, deterministic health features, private knowledge retrieval, consent and deletion, and the Motclaw-to-Codex Harness primary model route with Hermes as an on-demand fallback.

The 16-day study software, monitoring, and first real-data sync start on delivery day. The day-16 outcome may only be produced after real time has elapsed.

### 2. Names and scope

- FitCrew is the product and brand.
- BodyOS is the user-facing health assistant inside FitCrew.
- Motclaw is the Agent runtime.
- Codex Harness is the primary model capability through existing subscription OAuth; Hermes is on-demand fallback only.
- Feishu is the visible account entry; `fitcrew_user_id` is the immutable ownership key.
- Apple Health is optional and never a prerequisite for non-Apple functionality.

This Alpha processes real health data only for the owner. The 5-20 person real-health pilot, TestFlight, WHOOP, WeCom, acquisition channels, overseas channels, mainland production, and ICP are excluded.

### 3. Single-host architecture

The existing Tencent Cloud Tokyo Lighthouse is the only cloud resource. A minimal Docker Compose deployment fits the CNY-0 constraint and 2-vCPU/4-GB host: resident API, worker, PostgreSQL, reverse proxy, and Motclaw, with Hermes started only when needed. Paid managed services and a separate vector database are not created without an existing included allowance.

### 4. Data and authorization

Authorization is purpose- and scope-based. Raw health data and private knowledge are never available in group scope. Group calls to private, health, or private-knowledge tools return a deterministic `403`. Group output is generated from a fixed set of user-confirmed behavior tokens.

Every operation carries user, purpose, scope, data categories, consent, and retention context. Withdrawal immediately stops ingestion, retrieval, model processing, and sharing.

### 5. Health data

The iOS Bridge reads the minimum HealthKit set: glucose, sleep summaries, HRV, resting heart rate, workouts, active energy, steps, stand, and activity rings. Yuwell uses the Yuwell Anytime-to-Apple-Health path first.

Samples retain provenance, device, timestamps, original and normalized units, sync batch, and HealthKit UUID. Raw values are application-encrypted. Sync is incremental, retryable, and idempotent, with day-16 reconciliation. Raw detail is retained for 30 days; authorized daily aggregates and insights for up to 13 months.

Deterministic features cover data quality, glucose summaries and windows, overnight stability, sleep, HRV, resting heart rate, workouts, and activity. Models never receive raw health time series.

### 6. BodyOS and model routing

DM provides sync status, quality, evidenced private insights, knowledge Q&A, consent, withdrawal, export, and deletion. Group behavior is limited to confirmed low-sensitivity tokens. Unconsented all-group reading and all-member proactive reports are disabled.

Motclaw uses Codex Harness first. Bounded retries and circuit breaking precede an on-demand Hermes fallback. If both routes fail, work is queued and processing fails closed; no paid API fallback is configured.

### 7. Knowledge and demand pools

The three local PDFs are private owner sources. They never enter Git or the public knowledge base. Import retains hash, bibliography, page, version, rights status, and timestamp; encrypted chunks support page-cited retrieval. Answers distinguish book claims, primary evidence, owner data, and model inference.

Public knowledge and demand items follow the approved provenance, review, versioning, and audit workflows. Private health data, identities, and raw group messages never enter the public base.

### 8. GitHub and release

`flicy/fitcrew-agent` is the source repository. All work reaches `main` through a PR from `codex/v2-owner-alpha` with CI. The PR is not merged without user approval. Deployment records the tested PR SHA; `v2.0.0-alpha.1` is created only after approval and merge. `flicy/cola-pages` remains deployment-only and its current URL stays live.

### 9. Security and operations gates

Default deny, least privilege, no sensitive logs, secret-safe builds, real backup/restore/rollback, and negative cross-scope tests are mandatory. Existing V1 data and the stale dirty local checkout are preserved. Test messages are restricted to the designated BodyOS test conversations.

### 10. Same-day acceptance

Same-day software completion requires verifiable PR/CI, owner-only cloud deployment, first real HealthKit/Yuwell sync, BodyOS DM and group-token flows, retrieval over all three private PDFs, primary/fallback model tests, export/withdrawal/deletion, security tests, and rollback evidence. Physical device or account approval must be reported as one minimal user action and may not be replaced by fabricated real-data evidence.
