#!/bin/bash
# FitCrew · 给一个群开通标准健康节奏。
#
# 用法：
#   ./add-group.sh <profile> <chat_id> <群名> <theme>
#   theme: system(系统健身) | buddy(搭子打卡) | wellness(轻量养生)
#
# 例：
#   ./add-group.sh fitcrew oc_bebdb4d6... 健康搭子打卡群 buddy
#
# 会做两件事：① 建最小群档案 ② 安全写入 allowlist group_rule。
set -eu

PROFILE="${1:?用法: add-group.sh <profile> <chat_id> <群名> <theme>}"
CHAT_ID="${2:?缺 chat_id}"
GROUP_NAME="${3:?缺 群名}"
THEME="${4:-buddy}"

if [[ ! "$CHAT_ID" =~ ^oc_[0-9a-fA-F]+$ ]]; then echo "无效 chat_id"; exit 1; fi
case "$THEME" in system|buddy|wellness) ;; *) echo "未知 theme"; exit 1 ;; esac

HERE="$(cd "$(dirname "$0")" && pwd)"
HERMES_PY="${HERMES_PY:-$HOME/.hermes/hermes-agent/venv/bin/python}"
PROFILE_DIR="$HOME/.hermes/profiles/$PROFILE"
GROUPS_DIR="$PROFILE_DIR/memories/groups"
SAFE_NAME="$(echo "$GROUP_NAME" | tr -cd '[:alnum:]_-' | cut -c1-48)"
SAFE_NAME="${SAFE_NAME:-group}"
ARCHIVE="$GROUPS_DIR/${CHAT_ID}_${SAFE_NAME}.md"

echo "→ FitCrew add-group: profile=$PROFILE chat=$CHAT_ID 群=$GROUP_NAME theme=$THEME"

# ① 建群档案
mkdir -p "$GROUPS_DIR"
if [ -f "$ARCHIVE" ]; then
  echo "  档案已存在，跳过：$ARCHIVE"
else
  case "$THEME" in
    system)   PERSONA="系统健身：训练+饮食+恢复" ;;
    buddy)    PERSONA="搭子结伴打卡：找人一起把健康行动坚持下去" ;;
    wellness) PERSONA="轻量养生：弱数据、强鼓励，以积极心理暗示为锚" ;;
  esac
  cat > "$ARCHIVE" <<EOF
# 群档案 · $GROUP_NAME

- **chat_id**: \`$CHAT_ID\`
- **群名**: $GROUP_NAME
- **创建/加入时间**: $(date +%Y-%m-%d)
- **主题人格**: $PERSONA

## 群输出范围 / Group output boundary
- 只允许固定低敏行为令牌；个性化建议请私聊 BodyOS。
- Only fixed low-sensitivity behavior tokens are allowed; private coaching stays in DM.

## 隔离提醒
- 本群只引用本群公开消息与本档案；不得引用其他群或任何 private/ 内容。
EOF
  echo "  已建档案：$ARCHIVE"
fi

# ② 安全写入 config group_rule；Owner Alpha 群聊始终要求 @。
"$HERMES_PY" "$HERE/add_group_rule.py" "$PROFILE_DIR" "$CHAT_ID" --require-mention true

echo "→ 完成。执行 gateway restart 生效："
echo "   $HERMES_PY -m hermes_cli.main --profile $PROFILE gateway restart"
