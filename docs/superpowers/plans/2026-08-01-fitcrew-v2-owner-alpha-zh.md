# FitCrew / BodyOS V2 Owner-only Alpha 实施计划

> **供 Agent 执行：** 必须使用 superpowers:executing-plans，逐项执行本计划并用复选框追踪。

**目标：** 发布、测试、通过 PR 提交并部署一个 Owner-only FitCrew V2 Alpha，把私人 HealthKit/鱼跃数据和私人书籍知识安全接入 BodyOS，同时确保群聊与模型都无法取得原始健康数据。

**架构：** 现有腾讯云 Lighthouse 用 Docker Compose 运行 FastAPI、Worker 和 PostgreSQL。iOS HealthKit Bridge 上传加密、幂等批次；BodyOS 只能通过带 scope 的工具 API 访问数据；Motclaw 优先使用 Codex Harness，Hermes 按需备用；三本私人书以加密分段进行本人检索。

**技术栈：** Python 3.11+、FastAPI、SQLAlchemy、PostgreSQL、Alembic、AES-GCM、pytest、Swift/SwiftUI/HealthKit、XcodeGen、Docker Compose、Caddy、GitHub Actions。

---

## 文件职责

- `apps/api/bodyos_api/`：HTTP API、配置、数据库、策略、加密、健康、知识、记忆、BodyOS 与模型路由。
- `apps/api/tests/`：使用隔离 SQLite 与假 Provider 的单元及集成测试。
- `apps/worker/bodyos_worker/`：保留期、特征、发件箱、备份检查和实验节点。
- `apps/ios-bridge/`：HealthKit Bridge、设备绑定、增量同步和测试。
- `packages/contracts/`：iOS、API、Agent 工具和测试共享的 JSON Schema。
- `agent/`：BodyOS 运行规则和受限工具契约。
- `scripts/`：安全安装器、书籍导入器、BodyOS 工具、部署和证据脚本。
- `infra/tencent/`：Compose、容器、反向代理、环境示例、备份、恢复和回滚。
- `.github/`：CI、PR 模板、代码所有权和安全策略。
- `docs/`：双语产品、隐私、部署、运行手册、证据和实验文档。

### 任务 1：锁定设计和仓库安全

**文件：**
- 新建：`docs/superpowers/specs/2026-08-01-fitcrew-v2-owner-alpha-design.md`
- 新建：本中英文计划文件
- 修改：`.gitignore`

- [ ] 验证远端 `main` 的隔离基线：运行 `bash -n install.sh scripts/add-group.sh && python3 -m json.tool cron/jobs.seed.json >/dev/null`，期望退出码 0。
- [ ] 忽略 `.env*`、`data/`、`backups/`、私人证据、SQLite、PDF、签名文件、Xcode 用户数据和健康导出。
- [ ] 用脚本检查双语覆盖和未解决标记，期望没有残留标记。
- [ ] 运行 `git add docs/superpowers .gitignore && git commit -m "docs: lock V2 owner alpha design"`。

### 任务 2：建立可测试 API 和数据库

**文件：**
- 新建：`pyproject.toml`
- 新建：`apps/api/bodyos_api/{__init__,app,config,db,models,schemas}.py`
- 新建：`apps/api/tests/{conftest,test_healthcheck,test_schema}.py`
- 新建：`packages/contracts/health-sync-v1.schema.json`
- 新建：Alembic 配置和 `0001_owner_alpha.py`

- [ ] 先写失败测试：`GET /healthz` 必须返回版本；同步批次必须包含批次、设备、授权、来源、时间、单位和样本。
- [ ] 运行指定 pytest，确认因模块与契约不存在而失败。
- [ ] 实现用户、身份、设备、授权、同步批次、加密样本、日特征、洞察、记忆、知识、需求、审计和发件箱表及唯一约束。
- [ ] 运行 pytest 和 `alembic upgrade head`，确认测试和迁移成功。
- [ ] 提交 `feat: add owner alpha API foundation`。

### 任务 3：强制加密、授权、scope 和 DLP

**文件：**
- 新建：`apps/api/bodyos_api/{crypto,consent,policy,dlp,audit}.py`
- 新建：`apps/api/tests/{test_crypto,test_consent,test_policy,test_dlp}.py`

- [ ] 先写 AES-GCM 往返/篡改、按类别与目的授权、立即撤回、群调用健康/私人/私人知识拒绝、固定行为令牌和 DLP 测试。
- [ ] 运行测试，确认因模块不存在而失败。
- [ ] 实现版本化 AES-GCM 密钥、scope/purpose/category/token 枚举、默认拒绝授权、无正文审计和只接受已确认 token 的群发件箱。
- [ ] 运行测试并确认全部通过。
- [ ] 提交 `feat: enforce consent scopes and output DLP`。

### 任务 4：健康数据接入与确定性特征

**文件：**
- 新建：`apps/api/bodyos_api/{health_routes,health_service,features}.py`
- 新建：`apps/api/tests/{test_health_ingest,test_features,test_health_export_delete}.py`
- 新建：`apps/worker/bodyos_worker/{__init__,retention,study}.py`

- [ ] 先写授权上传、缺少授权、错绑、批次重放、样本去重、单位转换、时区和加密落盘测试。
- [ ] 运行测试，确认功能缺失造成失败。
- [ ] 实现绑定、授权、同步、状态、特征、导出、撤回和删除接口。
- [ ] 实现数据质量、血糖摘要/窗口、夜间稳定、睡眠、HRV、静息心率、锻炼与活动特征。
- [ ] 实现 30 天原始保留、13 个月聚合保留和第 3/8/15/16 天作业；第 16 天只请求真实全量对账。
- [ ] 运行测试并提交 `feat: add encrypted HealthKit ingestion and features`。

### 任务 5：私人知识与审核需求池

**文件：**
- 新建：`apps/api/bodyos_api/{knowledge,knowledge_routes,demand}.py`
- 新建：`apps/api/tests/{test_knowledge,test_demand}.py`
- 新建：`scripts/import_private_books.py`
- 新建：`docs/knowledge/private-book-register.example.json`

- [ ] 先写加密分段、页码引用、本人权限、公共已发布过滤、审核状态、来源撤回和需求状态测试。
- [ ] 运行测试，确认服务缺失造成失败。
- [ ] 用 `pypdf` 提取页文本、文件哈希、规范化、分段、加密和本人进程内词法检索；不把 PDF 复制到仓库或镜像。
- [ ] 实现来源、审核、适用性、版本和需求工作流 API。
- [ ] 运行测试并提交 `feat: add private knowledge and reviewed demand pools`。

### 任务 6：HealthKit Bridge

**文件：**
- 新建：`apps/ios-bridge/project.yml`
- 新建：SwiftUI App、HealthKitClient、SyncClient、KeychainStore、ConsentStore
- 新建：批次、游标和单位测试及 `Info.plist`

- [ ] 先写稳定批次 ID、成功后才推进游标、血糖单位转换、重试载荷和最小 HealthKit 类型测试。
- [ ] 运行 Swift 测试，确认核心包不存在而失败。
- [ ] 实现可测试核心和 SwiftUI App：显式授权、Keychain 设备凭据、增量同步、最后同步/质量展示和全量对账动作。
- [ ] 本机有完整 Xcode 时本机构建；否则在 macOS GitHub Actions 运行 XcodeGen 与 simulator build/test，期望退出码 0。
- [ ] 提交 `feat: add owner HealthKit bridge`。

### 任务 7：BodyOS、飞书与模型路由

**文件：**
- 新建：BodyOS 和模型网关模块与测试、`scripts/bodyos_tool.py`
- 修改：Agent 规则、cron、配置、Watcher、安装器和加群脚本

- [ ] 先写私聊特征/知识、群 token、群健康拒绝、去标识化模型包、主路径、重试、Hermes 备用、双失败关闭和重启队列测试。
- [ ] 先写重复 @、安装重复、无效群主题、默认开放和密钥明文输入的 V1 回归测试。
- [ ] 运行测试并确认正确失败。
- [ ] 实现受限工具、固定群 token、无正文模型日志、可配置 Codex Harness 与 Hermes 命令以及无付费回退。
- [ ] 修复 V1 回归，运行 pytest 和 Bash 语法检查并确认通过。
- [ ] 提交 `feat: connect scoped BodyOS and stable model routing`。

### 任务 8：部署、备份和运维

**文件：**
- 新建：`infra/tencent/` 下 Compose、Dockerfile、Caddy、环境示例、部署、备份、恢复和回滚
- 新建：双语部署/回滚、隐私/保留和 16 天实验手册
- 新建：无敏感日志测试

- [ ] 先写非 root、健康检查、资源限制、只读挂载、无收费服务、无秘密示例、无正文日志、加密备份和回滚 SHA 检查。
- [ ] 运行 pytest 和 Compose config，确认文件不存在造成失败；本机无 Docker 时在 CI/服务器验证 Compose。
- [ ] 实现固定镜像、本地 PostgreSQL、安全入口、加密备份、迁移优先、健康切换和按 SHA 回滚。
- [ ] 运行测试并提交 `ops: add zero-cost Tencent deployment and rollback`。

### 任务 9：CI、评审、版本和官网

**文件：**
- 新建：GitHub Actions、PR 模板、CODEOWNERS、`SECURITY.md`、`LICENSE`
- 修改：README、CHANGELOG、Landing

- [ ] CI 运行 Python、Ruff、JSON/YAML、ShellCheck、秘密扫描、Compose、Swift core 和 iOS simulator 构建，且不上传敏感产物。
- [ ] 双语更新公开文档，修复失效链接，说明 Owner-only、HealthKit 可选和私人数据/书籍永不提交。
- [ ] 运行全套本地验证并确认退出码 0。
- [ ] 提交 `chore: add V2 CI governance and release docs`，推送分支。
- [ ] 创建标题为 `feat: ship FitCrew V2 owner-only alpha` 的 PR，正文写范围、测试、部署、隐私、回滚和物理检查点。

### 任务 10：部署和新鲜证据

**文件：**
- 新建：`docs/evidence/2026-08-01-owner-alpha-verification.md`

- [ ] 只读盘点服务器系统、资源、端口、容器、服务、TLS、备份和回滚目标，不把 IP 或秘密写进 Git。
- [ ] 部署测试过的 PR SHA，主机秘密权限 `0600`，迁移后启动，健康检查通过才接测试流量。
- [ ] 在 Git 外导入三本 PDF，加密分段，只记录脱敏数量和哈希。
- [ ] 运行跨群金丝雀、群 `403`、撤回、DLP、错绑、日志、导出、删除、备份、恢复和回滚测试。
- [ ] 只在指定本人私聊和测试群做知识引用、行为 token、模型主路径、备用注入和重启恢复测试。
- [ ] 在本人 iPhone 授权最小数据，绑定并上传真实批次，只证明脱敏记录数、来源、时间窗、单位/时区质量和同步状态；启动第 3/8/15/16 天作业。
- [ ] 再跑完整测试、构建、差异和秘密扫描，检查云健康，并用精确 SHA、CI、部署版本、脱敏证据、风险和回滚更新 PR。

期望最终每项当天验收都有证据，或被明确记录为需要一次用户物理/账号动作的外部阻塞；不得提前声称已有第 16 天结果。
