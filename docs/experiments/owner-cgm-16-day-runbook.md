# Owner CGM 16-Day Runbook / Owner CGM 16 天手册

## 中文

CGM 是持续葡萄糖监测（Continuous Glucose Monitoring）。本轮使用鱼跃 Anytime 5 Pro 约 16 天；若鱼跃 App 已把数据写入 Apple 健康，HealthKit Bridge 从 Apple 健康统一读取。OpenAI Health 中已授权的数据不能作为 FitCrew 的服务器数据源：Apple Health 访问必须由本人设备上的 HealthKit App 单独授权，第三方服务不能替 FitCrew 转授。

### 启动日

1. 在 iPhone 安装并打开 FitCrew Health Bridge，扫描私有 `owner-pairing.png`。
2. 逐项确认 Apple 健康最小读取权限；不授权的 category 保持不可用，不影响飞书账号和其他功能。
3. 点击“立即增量同步”，再检查 App 状态与服务 `/v1/health/status` 的脱敏样本数、来源时间窗和 `last_sync_at`。不在证据里展示真实数值。
4. 在指定的 Owner 私聊询问一次血糖、睡眠和运动建议，验证回答引用私人书名/页码、只用聚合特征且不诊断。
5. 在指定测试群分别触发五种行为意图，确认只返回固定 token；使用非白名单群和错误身份做拒绝测试。

### 16 天节奏

- 每日：后台增量同步；游标只有在所有 category 批次成功后推进。失败时下次重试，不丢数据。
- 第 3、8、15 天：Worker 创建阶段总结事件，BodyOS 只能基于截至当日的聚合和数据质量说明趋势。
- 第 16 天：App 执行 30 天窗口全量对账，批次标记 `full_reconciliation=true`；服务按 sample ID 去重。当天只证明对账执行，不能提前生成不存在的第 16 天结果。
- 第 30 天后：原始明细自动删除；日聚合与经授权洞察按 13 个月保留策略处理。

### 质量与中止条件

记录设备/来源、时区、单位转换、重复数、期望点数与完整度。鱼跃 mmol/L 在服务端统一转换为 mg/dL；原单位仍作为元数据保留。出现明显设备异常、严重不适、疑似低/高血糖急症或医生要求停用时，停止实验并优先寻求医疗帮助。BodyOS 不据此调整药物。

WHOOP 不属于本轮依赖。当前 Apple Watch/Health 已覆盖活动、训练、能量、步数、站立、睡眠、HRV 与静息心率；等 16 天数据证明恢复/负荷洞察仍有稳定缺口后，再决定是否增加 WHOOP，避免先买硬件再寻找问题。

## English

CGM means Continuous Glucose Monitoring. This run uses the Yuwell Anytime 5 Pro for about 16 days. If the Yuwell app writes to Apple Health, the HealthKit Bridge reads it through that unified store. Data authorized in OpenAI Health cannot serve as FitCrew's server source: HealthKit access requires separate authorization by the owner in an app on the device, and a third party cannot re-grant it to FitCrew.

### Start day

1. Install and open FitCrew Health Bridge on the iPhone, then scan the private `owner-pairing.png`.
2. Confirm each minimum Apple Health read category. A category left unauthorized remains unavailable without affecting the Feishu account or other functions.
3. Tap “incremental sync,” then inspect the app and `/v1/health/status` for de-identified sample count, source window, and `last_sync_at`. Never put real values in evidence.
4. Ask one glucose, sleep, and activity question in the designated owner DM. Confirm the response cites private title/page references, uses aggregates only, and does not diagnose.
5. Trigger all five behavior intents in the designated test group and confirm fixed tokens only. Test denial from a non-allowlisted group and wrong identity.

### Sixteen-day cadence

- Daily: background incremental sync. The cursor advances only after all category batches succeed; a failure retries next time without data loss.
- Days 3, 8, and 15: the worker creates a stage-summary event. BodyOS may describe trends only from aggregates and quality available by that day.
- Day 16: the app performs a full 30-day reconciliation with `full_reconciliation=true`; the service deduplicates by sample ID. This proves reconciliation on that day and never invents a day-16 result early.
- After day 30: raw detail is deleted; daily aggregates and authorized insights follow the 13-month policy.

### Quality and stop conditions

Record device/source, timezone, unit conversion, duplicate count, expected points, and completeness. The service normalizes Yuwell mmol/L to mg/dL while preserving the original unit as metadata. Stop the experiment and seek medical help first for clear device malfunction, severe symptoms, suspected urgent low/high glucose, or a clinician's instruction. BodyOS does not adjust medication.

WHOOP is not a dependency for this run. Apple Watch/Health already cover activity, workouts, energy, steps, stand time, sleep, HRV, and resting heart rate. Reconsider WHOOP only if the 16-day data demonstrates a stable recovery/load insight gap, avoiding hardware purchase before a validated problem.
