#!/bin/bash
# Body OS · AI 健身管理专家 —— 一键安装到一个新的 Hermes profile。
#
# 用法（推荐用环境变量传参，避免交互）：
#   BODYOS_PROFILE=bodyos \
#   FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx FEISHU_HOME_CHANNEL=oc_xxx \
#   BODYOS_MODEL=deepseek-v4-flash BODYOS_BASE_URL=https://token.sensenova.cn/v1 BODYOS_API_KEY=sk-xxx \
#   ./install.sh
#
# 未提供的参数会交互式询问。
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
HERMES_PY="${HERMES_PY:-$HOME/.hermes/hermes-agent/venv/bin/python}"
HERMES_ROOT="$HOME/.hermes"

ask() { # ask VARNAME prompt
  local var="$1" prompt="$2"
  if [ -z "${!var:-}" ]; then read -r -p "$prompt" "$var"; fi
}

echo "═══════════════════════════════════════════════"
echo "  Body OS · AI 健身管理专家 安装程序"
echo "═══════════════════════════════════════════════"

ask BODYOS_PROFILE      "Profile 名（默认 bodyos）: "
BODYOS_PROFILE="${BODYOS_PROFILE:-bodyos}"
ask FEISHU_APP_ID        "飞书 App ID: "
ask FEISHU_APP_SECRET    "飞书 App Secret: "
ask FEISHU_HOME_CHANNEL  "管理单聊 chat_id (FEISHU_HOME_CHANNEL): "
ask BODYOS_MODEL        "推理模型（默认 deepseek-v4-flash）: "
BODYOS_MODEL="${BODYOS_MODEL:-deepseek-v4-flash}"
ask BODYOS_BASE_URL     "推理 base_url（默认 https://token.sensenova.cn/v1）: "
BODYOS_BASE_URL="${BODYOS_BASE_URL:-https://token.sensenova.cn/v1}"
ask BODYOS_API_KEY      "推理 API key: "

PROFILE_DIR="$HERMES_ROOT/profiles/$BODYOS_PROFILE"
echo "→ 目标 profile: $PROFILE_DIR"

# ① 建 profile 目录（若不存在）
mkdir -p "$PROFILE_DIR"

# ② 复制 agent 身份文件
echo "→ 写入身份文件 AGENTS.md / SOUL.md / HERMES.md"
cp "$HERE/agent/AGENTS.md" "$HERE/agent/SOUL.md" "$HERE/agent/HERMES.md" "$PROFILE_DIR/"

# ③ 渲染 config.yaml
echo "→ 渲染 config.yaml"
sed -e "s#__MODEL__#$BODYOS_MODEL#g" \
    -e "s#__BASE_URL__#$BODYOS_BASE_URL#g" \
    -e "s#__API_KEY__#$BODYOS_API_KEY#g" \
    "$HERE/config/config.template.yaml" > "$PROFILE_DIR/config.yaml"

# ④ 渲染 .env
echo "→ 渲染 .env"
sed -e "s#__PROFILE_DIR__#$PROFILE_DIR#g" \
    -e "s#__FEISHU_APP_ID__#$FEISHU_APP_ID#g" \
    -e "s#__FEISHU_APP_SECRET__#$FEISHU_APP_SECRET#g" \
    -e "s#__FEISHU_HOME_CHANNEL__#$FEISHU_HOME_CHANNEL#g" \
    -e "s#__API_KEY__#$BODYOS_API_KEY#g" \
    -e "s#__BASE_URL__#$BODYOS_BASE_URL#g" \
    "$HERE/config/env.template" > "$PROFILE_DIR/.env"
chmod 600 "$PROFILE_DIR/.env"

# ⑤ 复制记忆种子与脚本
echo "→ 复制记忆种子与脚本"
mkdir -p "$PROFILE_DIR/memories/groups" "$PROFILE_DIR/memories/private" "$PROFILE_DIR/memories/daily" "$PROFILE_DIR/scripts"
cp "$HERE/memories/MEMORY.md" "$HERE/memories/USER.md" "$PROFILE_DIR/memories/"
cp "$HERE/memories/groups/_TEMPLATE.md" "$PROFILE_DIR/memories/groups/"
cp "$HERE/memories/private/_TEMPLATE.md" "$PROFILE_DIR/memories/private/"
cp "$HERE/memories/daily/README.md" "$PROFILE_DIR/memories/daily/"
cp "$HERE/scripts/feishu_group_watcher.py" "$HERE/scripts/add_group_rule.py" "$HERE/scripts/add-group.sh" "$PROFILE_DIR/scripts/"
chmod +x "$PROFILE_DIR/scripts/add-group.sh"

# ⑥ 校验 config.yaml 可解析（防止模板渲染出问题）
echo "→ 校验 config.yaml YAML 合法性"
"$HERMES_PY" -c "import yaml,sys; yaml.safe_load(open('$PROFILE_DIR/config.yaml')); print('  ✅ YAML OK')"

# ⑦ 加载通用定时任务（新群引导巡检 / @提及巡检 / 个人周度私聊小结）
echo "→ 加载通用定时任务"
BODYOS_PROFILE="$BODYOS_PROFILE" PROFILE_DIR="$PROFILE_DIR" HERE="$HERE" "$HERMES_PY" - <<'PY'
import json, os, subprocess
profile = os.environ["BODYOS_PROFILE"]
profile_dir = os.environ["PROFILE_DIR"]
here = os.environ["HERE"]
hermes_py = os.environ.get("HERMES_PY", os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python"))
seed = json.load(open(os.path.join(here, "cron", "jobs.seed.json")))
for j in seed["jobs"]:
    prompt = j["prompt"].replace("__PROFILE_DIR__", profile_dir)
    cmd = [hermes_py, "-m", "hermes_cli.main", "--profile", profile,
           "cron", "create", j["schedule"], prompt,
           "--name", j["name"], "--deliver", j["deliver"], "--profile", profile]
    for s in j.get("skills", []):
        cmd += ["--skill", s]
    if j.get("script"):
        cmd += ["--script", j["script"]]
    r = subprocess.run(cmd, capture_output=True, text=True)
    first = (r.stdout.strip() or r.stderr.strip()).splitlines()
    print("  ", j["name"], "=>", first[0] if first else "?")
PY

# ⑧ 安装并启动 gateway 服务
echo "→ 安装并启动 gateway 服务"
"$HERMES_PY" -m hermes_cli.main --profile "$BODYOS_PROFILE" gateway install >/dev/null 2>&1 || true
"$HERMES_PY" -m hermes_cli.main --profile "$BODYOS_PROFILE" gateway restart

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ Body OS 安装完成！"
echo "═══════════════════════════════════════════════"
echo ""
echo "下一步："
echo "  1. 在飞书把这个机器人拉进你的健康群。"
echo "  2. 「新群引导巡检」每 10 分钟会自动发现新群、建档并发引导消息。"
echo "  3. 给某个群开通每日打卡/复盘/周报节奏："
echo "       $PROFILE_DIR/scripts/add-group.sh $BODYOS_PROFILE <chat_id> <群名> <system|buddy|wellness>"
echo "     然后重启 gateway 生效。"
echo "  4. 看日志： tail -f $PROFILE_DIR/logs/gateway.log"
echo ""
echo "⚠️ 提醒：不要手工直接编辑 config.yaml（用 add-group.sh 或 Moticlaw 正常流程）。"
