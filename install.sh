#!/bin/bash
# FitCrew · AI 健身管理专家 —— 一键安装到一个新的 Hermes profile。
#
# 用法（推荐用环境变量传参，避免交互）：
#   FITCREW_PROFILE=fitcrew \
#   FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx FEISHU_HOME_CHANNEL=oc_xxx \
#   BODYOS_API_BASE=https://bodyos.example.com BODYOS_INTERNAL_TOKEN=... \
#   BODYOS_MODEL_PROXY_TOKEN=... \
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

ask_secret() { # ask VARNAME prompt without terminal echo
  local var="$1" prompt="$2"
  if [ -z "${!var:-}" ]; then
    read -r -s -p "$prompt" "$var"
    echo ""
  fi
}

echo "═══════════════════════════════════════════════"
echo "  FitCrew · AI 健身管理专家 安装程序"
echo "═══════════════════════════════════════════════"

ask FITCREW_PROFILE      "Profile 名（默认 fitcrew）: "
FITCREW_PROFILE="${FITCREW_PROFILE:-fitcrew}"
ask FEISHU_APP_ID        "飞书 App ID: "
ask_secret FEISHU_APP_SECRET    "飞书 App Secret（输入不回显）: "
ask FEISHU_HOME_CHANNEL  "管理单聊 chat_id (FEISHU_HOME_CHANNEL): "
ask BODYOS_API_BASE      "BodyOS API 地址（https://...）: "
ask_secret BODYOS_INTERNAL_TOKEN "BodyOS 内部令牌（输入不回显）: "
ask_secret BODYOS_MODEL_PROXY_TOKEN "BodyOS 模型代理令牌（输入不回显）: "
BODYOS_MODEL_BASE_URL="${BODYOS_API_BASE%/}/v1"

PROFILE_DIR="$HERMES_ROOT/profiles/$FITCREW_PROFILE"
echo "→ 目标 profile: $PROFILE_DIR"

# ① 建 profile 目录（若不存在）
mkdir -p "$PROFILE_DIR"

# ② 复制 agent 身份文件
echo "→ 写入身份文件 AGENTS.md / SOUL.md / HERMES.md"
cp "$HERE/agent/AGENTS.md" "$HERE/agent/SOUL.md" "$HERE/agent/HERMES.md" "$PROFILE_DIR/"

# ③ 渲染 config.yaml
echo "→ 渲染 config.yaml"
sed -e "s#__BODYOS_MODEL_BASE_URL__#$BODYOS_MODEL_BASE_URL#g" \
    "$HERE/config/config.template.yaml" > "$PROFILE_DIR/config.yaml"

# ④ 渲染 .env
echo "→ 渲染 .env"
sed -e "s#__PROFILE_DIR__#$PROFILE_DIR#g" \
    -e "s#__FEISHU_APP_ID__#$FEISHU_APP_ID#g" \
    -e "s#__FEISHU_APP_SECRET__#$FEISHU_APP_SECRET#g" \
    -e "s#__FEISHU_HOME_CHANNEL__#$FEISHU_HOME_CHANNEL#g" \
    -e "s#__BODYOS_API_BASE__#$BODYOS_API_BASE#g" \
    -e "s#__BODYOS_INTERNAL_TOKEN__#$BODYOS_INTERNAL_TOKEN#g" \
    -e "s#__BODYOS_MODEL_PROXY_TOKEN__#$BODYOS_MODEL_PROXY_TOKEN#g" \
    -e "s#__BODYOS_MODEL_BASE_URL__#$BODYOS_MODEL_BASE_URL#g" \
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

# ⑤b 安装模型前置隐私 Guard 和 gateway envelope hook（仅此 profile 生效）
echo "→ 安装 BodyOS 模型前置隐私边界"
mkdir -p "$PROFILE_DIR/plugins/bodyos_guard" "$PROFILE_DIR/hooks/bodyos-envelope"
cp "$HERE/integrations/hermes/bodyos_guard/plugin.yaml" \
   "$HERE/integrations/hermes/bodyos_guard/__init__.py" \
   "$PROFILE_DIR/plugins/bodyos_guard/"
cp "$HERE/integrations/hermes/gateway_hook/HOOK.yaml" \
   "$HERE/integrations/hermes/gateway_hook/handler.py" \
   "$PROFILE_DIR/hooks/bodyos-envelope/"
mkdir -p "$PROFILE_DIR/.bodyos-sanitized"
chmod 700 "$PROFILE_DIR/.bodyos-sanitized" "$PROFILE_DIR/hooks/bodyos-envelope"

# ⑥ 校验 config.yaml 可解析（防止模板渲染出问题）
echo "→ 校验 config.yaml YAML 合法性"
"$HERMES_PY" -c "import yaml,sys; yaml.safe_load(open('$PROFILE_DIR/config.yaml')); print('  ✅ YAML OK')"

# ⑦ 加载不调用模型的群聊安全巡检（按名称幂等）
echo "→ 加载通用定时任务"
FITCREW_PROFILE="$FITCREW_PROFILE" PROFILE_DIR="$PROFILE_DIR" HERE="$HERE" "$HERMES_PY" - <<'PY'
import json, os, subprocess
profile = os.environ["FITCREW_PROFILE"]
profile_dir = os.environ["PROFILE_DIR"]
here = os.environ["HERE"]
hermes_py = os.environ.get("HERMES_PY", os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python"))
seed = json.load(open(os.path.join(here, "cron", "jobs.seed.json")))
existing = subprocess.run(
    [hermes_py, "-m", "hermes_cli.main", "--profile", profile, "cron", "list", "--all"],
    capture_output=True,
    text=True,
).stdout
for j in seed["jobs"]:
    if j["name"] in existing:
        print("  ", j["name"], "=> already installed")
        continue
    prompt = j.get("prompt", "").replace("__PROFILE_DIR__", profile_dir)
    cmd = [hermes_py, "-m", "hermes_cli.main", "--profile", profile,
           "cron", "create", j["schedule"], prompt,
           "--name", j["name"], "--deliver", j["deliver"]]
    for s in j.get("skills", []):
        cmd += ["--skill", s]
    if j.get("script"):
        cmd += ["--script", j["script"]]
    if j.get("no_agent"):
        cmd += ["--no-agent"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    first = (r.stdout.strip() or r.stderr.strip()).splitlines()
    print("  ", j["name"], "=>", first[0] if first else "?")
PY

# ⑧ 安装并启动 gateway 服务
echo "→ 安装并启动 gateway 服务"
"$HERMES_PY" -m hermes_cli.main --profile "$FITCREW_PROFILE" gateway install >/dev/null 2>&1 || true
"$HERMES_PY" -m hermes_cli.main --profile "$FITCREW_PROFILE" gateway restart

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ FitCrew 安装完成！"
echo "═══════════════════════════════════════════════"
echo ""
echo "下一步："
echo "  1. 在飞书把这个机器人拉进你的健康群。"
echo "  2. 「BodyOS群聊安全巡检」每 5 分钟处理已加入白名单群的 @提及。"
echo "  3. 把某个群加入白名单："
echo "       $PROFILE_DIR/scripts/add-group.sh $FITCREW_PROFILE <chat_id> <群名> <system|buddy|wellness>"
echo "     然后重启 gateway 生效。"
echo "  4. 看日志： tail -f $PROFILE_DIR/logs/gateway.log"
echo ""
echo "⚠️ 提醒：群聊只输出固定低敏行为令牌；个性化建议只在私聊。"
