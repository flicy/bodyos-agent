# Memory Policy / 记忆策略

## 中文

当前 Owner-only Alpha 的可信记忆存储是 BodyOS 加密数据库。文件型记忆只保存非敏感模板与运行规则，不保存真实飞书 ID、聊天正文、健康数据、诊断、联系方式或私人书摘。

- 群与群、群与个人严格隔离；群聊只返回固定行为 token。
- 本人确认的稳定偏好进入私人加密记忆，并带来源、scope、确认状态与过期时间。
- 原始健康明细保留 30 天；授权的日聚合与洞察保留 13 个月。
- 公共知识和需求先进入候选池，经来源、权利、适用范围与审核状态核验后才能发布。

## English

The encrypted BodyOS database is the trusted memory store for the owner-only Alpha. File memory contains only non-sensitive templates and runtime rules—never real Feishu IDs, chat text, health data, diagnoses, contact details, or private excerpts.

- Isolate group-to-group and group-to-person scopes; groups return fixed behavior tokens only.
- Owner-confirmed stable preferences enter encrypted private memory with provenance, scope, confirmation status, and expiry.
- Raw health detail is retained for 30 days; authorized daily aggregates and insights for 13 months.
- Public knowledge and demands first enter candidate pools and require source, rights, applicability, and review checks before publication.
