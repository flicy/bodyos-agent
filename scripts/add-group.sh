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
# 会做三件事：① 建群档案 ② 按 theme 建该群的节奏 cron ③ 安全写入 config group_rule。
set -eu

PROFILE="${1:?用法: add-group.sh <profile> <chat_id> <群名> <theme>}"
CHAT_ID="${2:?缺 chat_id}"
GROUP_NAME="${3:?缺 群名}"
THEME="${4:-buddy}"

HERE="$(cd "$(dirname "$0")" && pwd)"
HERMES_PY="${HERMES_PY:-$HOME/.hermes/hermes-agent/venv/bin/python}"
PROFILE_DIR="$HOME/.hermes/profiles/$PROFILE"
GROUPS_DIR="$PROFILE_DIR/memories/groups"
SAFE_NAME="$(echo "$GROUP_NAME" | tr ' /' '__')"
ARCHIVE="$GROUPS_DIR/oc_${CHAT_ID#oc_}"
ARCHIVE="$GROUPS_DIR/${CHAT_ID}_${SAFE_NAME}.md"

echo "→ FitCrew add-group: profile=$PROFILE chat=$CHAT_ID 群=$GROUP_NAME theme=$THEME"

# ① 建群档案
mkdir -p "$GROUPS_DIR"
if [ -f "$ARCHIVE" ]; then
  echo "  档案已存在，跳过：$ARCHIVE"
else
  case "$THEME" in
    system)   PERSONA="系统健身：训练+饮食+恢复"; RHYTHM="每天 08:30 早打卡 / 20:30 晚复盘 / 周日 21:00 周报"; RM=false ;;
    buddy)    PERSONA="搭子结伴打卡：找人一起把健康行动坚持下去"; RHYTHM="每天 08:30 早打卡 / 20:30 晚复盘 / 周日 21:00 周报"; RM=false ;;
    wellness) PERSONA="轻量养生：弱数据、强鼓励，以积极心理暗示为锚"; RHYTHM="每天 09:00 每日最小行动 / 21:00 晚间互赞"; RM=false ;;
    *) echo "未知 theme: $THEME（应为 system|buddy|wellness）"; exit 1 ;;
  esac
  cat > "$ARCHIVE" <<EOF
# 群档案 · $GROUP_NAME

- **chat_id**: \`$CHAT_ID\`
- **群名**: $GROUP_NAME
- **创建/加入时间**: $(date +%Y-%m-%d)
- **主题人格**: $PERSONA

## 成员 roster（open_id ↔ 昵称）
| 昵称 | open_id |
|---|---|
| （待补充——可经 lark-im --as user 列成员，或入群引导时成员自报） | — |

## 群专属节奏
- $RHYTHM

## 群内公开目标与约定
- （入群引导时请每位成员自报健康目标，沉淀到此处；仅公开目标）

## 隔离提醒
- 本群只引用本群公开消息与本档案；不得引用其他群或任何 private/ 内容。
EOF
  echo "  已建档案：$ARCHIVE"
fi

# ② 建该群节奏 cron
H() { "$HERMES_PY" -m hermes_cli.main --profile "$PROFILE" "$@"; }
DELIVER="feishu:$CHAT_ID"

case "$THEME" in
  system|buddy)
    H cron create "30 8 * * *" "你是 FitCrew 健身管理专家。现在是「$GROUP_NAME」的早晨打卡。只输出一条将直接发送到群里的简短中文消息，不调用任何工具，不提及体重或私人数据。邀请大家用一行打卡：今天的运动或健康计划。明确可跳过或降级，不追问。不要输出分析、标题说明或[SILENT]。" --name "$GROUP_NAME·早晨打卡" --deliver "$DELIVER" --profile "$PROFILE" >/dev/null
    H cron create "30 20 * * *" "你是 FitCrew 健身管理专家。现在是「$GROUP_NAME」的 30 秒晚间复盘。只输出一条将直接发送到群里的简短中文消息，不调用任何工具，不公开敏感数据。请参与者用一行回答：今天完成了什么、最大的阻力、明天愿意保留的一个最小行动。提醒评分看行为完成度，不比体重；漏答不惩罚。不要输出分析、标题说明或[SILENT]。" --name "$GROUP_NAME·晚间复盘" --deliver "$DELIVER" --profile "$PROFILE" >/dev/null
    H cron create "0 21 * * 0" "你是 FitCrew 健身管理专家，要为「$GROUP_NAME」生成周日低压力周报。只读取群 $CHAT_ID 最近7天与饮食、睡眠、运动、恢复、打卡和互相支持有关的公开消息；不要读取或泄露任何人的单聊、体重、围度、疾病、用药或其他私密信息。使用 lark-im 只读能力，最多读取最近200条群消息。按“本周做得好的行为、主要阻力、各自下周一个微目标、共同约定”输出一条简洁中文群消息；数据不足时明确说数据不足并发出复盘邀请，不编造。不要使用发送工具，最终输出会由定时任务直接投递。" --name "$GROUP_NAME·周日合作周报" --deliver "$DELIVER" --profile "$PROFILE" --skill lark-im --skill lark-shared >/dev/null
    echo "  已建节奏 cron：早打卡/晚复盘/周报"
    ;;
  wellness)
    H cron create "0 9 * * *" "你是 FitCrew 健身管理专家。现在是「$GROUP_NAME」的每日最小健康行动邀请。只输出一条将直接发送到群里的简短中文消息，不调用任何工具，不提及体重或私人数据。这个群主打轻松氛围，弱数据、强鼓励。邀请大家用一行说出今天愿意做的一个最小健康行动，并强调可跳过、不追问。不要输出分析、标题说明或[SILENT]。" --name "$GROUP_NAME·每日最小行动" --deliver "$DELIVER" --profile "$PROFILE" >/dev/null
    H cron create "0 21 * * *" "你是 FitCrew 健身管理专家。现在是「$GROUP_NAME」的晚间互赞时间。只输出一条将直接发送到群里的简短中文消息，不调用任何工具，不公开敏感数据。邀请大家用一行分享今天做到的一个健康小事，并互相点赞鼓励；语气温暖积极。不比较数据、不评判、漏答不惩罚。不要输出分析、标题说明或[SILENT]。" --name "$GROUP_NAME·晚间互赞" --deliver "$DELIVER" --profile "$PROFILE" >/dev/null
    echo "  已建节奏 cron：每日最小行动/晚间互赞"
    ;;
esac

# ③ 安全写入 config group_rule
"$HERMES_PY" "$HERE/add_group_rule.py" "$PROFILE_DIR" "$CHAT_ID" --require-mention "${RM:-false}"

echo "→ 完成。执行 gateway restart 生效："
echo "   $HERMES_PY -m hermes_cli.main --profile $PROFILE gateway restart"
