# FitCrew · AI 健身管理专家

一个**可加载的飞书 AI 健身管理专家 Agent 安装包**。一次安装，得到一个能管理多个健康群、并对每个人做私密个性化健康管理的 AI 助手。

> 产品背景与完整运行手册见同目录 [`PRODUCT.md`](../PRODUCT.md)；本包是它的**可复用安装产物**。

## 它能做什么

- **群运营**：管理多个健康群，每日打卡、晚间复盘/互赞、每周周报、同伴互助；每个群有独立人设和节奏。
- **个人私管理**：单聊里做入组评估、目标拆解、敏感数据跟踪、一对一建议、每周个人私聊小结。
- **专家大脑**：运动/营养/恢复/睡眠知识 + 行为科学（微习惯、看行为完成度不比体重、不复盘不惩罚）。
- **自动引导**：被拉入新群自动发引导消息，让成员主动说出健康目标。
- **隐私红线**：群与群、群与个人严格隔离；私密信息绝不进群。

## 目录结构

```
fitcrew-agent/
├── install.sh                 # 一键安装到新 Hermes profile
├── agent/                     # Agent 身份文件（装入 profile）
│   ├── AGENTS.md              # 角色与职责
│   ├── SOUL.md                # 性格与人设
│   └── HERMES.md              # 运行规则/操作手册（隔离红线、记忆结构、cron）
├── config/
│   ├── config.template.yaml   # 模型 + 飞书 + 群规则模板
│   └── env.template           # 飞书 + 推理凭据模板
├── memories/                  # 记忆种子
│   ├── MEMORY.md              # 隔离原则 + 群索引
│   ├── USER.md                # 全局偏好
│   ├── groups/_TEMPLATE.md    # 群档案模板
│   ├── private/_TEMPLATE.md   # 私人档案模板
│   └── daily/README.md        # 30 天明细规则
├── scripts/
│   ├── feishu_group_watcher.py  # @提及巡检（从 groups/ 自动推导群列表）
│   ├── add_group_rule.py        # 安全写 config group_rule（YAML 往返）
│   └── add-group.sh             # 给一个群开通标准节奏
├── cron/
│   └── jobs.seed.json         # 通用定时任务种子（新群引导/@巡检/周度私聊小结）
└── landing/index.html         # 产品介绍落地页
```

## 依赖

- macOS + [Hermes Agent](https://github.com/) 运行时（`~/.hermes/hermes-agent/`，含 venv）。Moticlaw 桌面应用自带。
- 一个飞书企业自建应用（拿到 App ID / App Secret），开启机器人能力与 im 消息读写权限。
- 一个 OpenAI 兼容的推理端点（默认 SenseNova：`https://token.sensenova.cn/v1` + `deepseek-v4-flash`）。
- `lark-cli`（@提及巡检脚本用）。

## 快速开始

```bash
cd fitcrew-agent

# 1) 安装（参数可用环境变量传，否则交互询问）
FITCREW_PROFILE=fitcrew \
FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx FEISHU_HOME_CHANNEL=oc_xxx \
FITCREW_MODEL=deepseek-v4-flash \
FITCREW_BASE_URL=https://token.sensenova.cn/v1 \
FITCREW_API_KEY=sk-xxx \
./install.sh

# 2) 在飞书把机器人拉进健康群
#    「新群引导巡检」每 10 分钟自动发现新群、建档、发引导消息

# 3) 给某个群开通每日打卡/复盘/周报节奏
~/.hermes/profiles/fitcrew/scripts/add-group.sh fitcrew oc_xxxxxxxx 健康搭子打卡群 buddy
#    theme: system(系统健身) | buddy(搭子打卡) | wellness(轻量养生)
~/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main --profile fitcrew gateway restart
```

## 安装做了什么

1. 建 profile，装入 `AGENTS.md`/`SOUL.md`/`HERMES.md` 身份文件。
2. 渲染 `config.yaml`（模型/飞书/群规则）与 `.env`（飞书 + 推理凭据）。
3. 铺好记忆种子（隔离原则、群/私人档案模板、30 天明细规则）与巡检脚本。
4. 加载 3 个通用定时任务（新群引导巡检 / @提及巡检 / 个人周度私聊小结）。
5. 安装并启动 gateway（launchd 服务，开机自启）。

## 定时任务一览

| 任务 | 时间 | 范围 | 来源 |
|---|---|---|---|
| 新群引导巡检 | 每 10 分钟 | 全部群 | install（通用） |
| @提及巡检 | 每 5 分钟 | 全部群 | install（通用，脚本） |
| 个人周度私聊小结 | 周日 20:00 | 每位成员单聊 | install（通用） |
| 群早打卡 / 晚复盘 / 周报 | 08:30 / 20:30 / 周日21:00 | 单个群 | add-group（system/buddy） |
| 每日最小行动 / 晚间互赞 | 09:00 / 21:00 | 单个群 | add-group（wellness） |

## 重要约定（务必遵守）

- ⚠️ **不要手工直接编辑 `config.yaml`**（尤其 group_rules）——YAML 写坏会导致 Hermes 静默回退默认配置，极隐蔽。用 `add-group.sh` 或 Moticlaw 正常流程。
- ⚠️ **新建定时任务一律用 `hermes cron create`**（落盘 jobs.json），别让任务只活在运行内存（重启会丢）。
- `.env` 必须同时有 `OPENAI_API_KEY` + `OPENAI_BASE_URL`，否则 cron/后台报 `No inference provider configured`。
- 隐私红线：群隔离 + 私密不可进群；不做医疗诊断。

## 自定义

- 改人设语气：编辑装入后的 `SOUL.md`。
- 改群主题/节奏：在 `add-group.sh` 的 theme 分支里调整 prompt 与时间。
- 改引导话术：`cron/jobs.seed.json` 与 `agent/HERMES.md` 中的引导消息模板。
