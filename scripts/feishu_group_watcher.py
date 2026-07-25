#!/usr/bin/env python3
"""Body OS @提及巡检脚本（可移植版）。

扫描所管理群中新出现的 @机器人 提及，输出 JSONL（每行一条），无新提及则静默。
管理的群从 memories/groups/ 目录自动推导（每个 <chat_id>_<名字>.md 即一个群），
因此给一个新群建档后，巡检会自动覆盖它，无需改代码。

可配置（环境变量）：
  BODYOS_PROFILE_DIR  profile 目录（默认：脚本所在目录的上一级）
  BODYOS_BOT_NAME     机器人在飞书的名字（默认 Moticlaw飞书助手）
  BODYOS_LARK_CLI     lark-cli 路径（默认从 PATH 找 lark-cli）
"""
import json, subprocess, os, sys, glob, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.environ.get("BODYOS_PROFILE_DIR") or os.path.dirname(SCRIPT_DIR)
GROUPS_DIR = os.path.join(PROFILE_DIR, "memories", "groups")
STATE_FILE = os.path.join(SCRIPT_DIR, ".feishu_watcher_state.json")
BOT_NAME = os.environ.get("BODYOS_BOT_NAME", "Moticlaw飞书助手")
LARK_CLI = os.environ.get("BODYOS_LARK_CLI", "lark-cli")


def load_groups():
    """从 groups/ 目录推导 (chat_id, name) 列表。
    文件名形如 oc_<hex>_<名字>.md；chat_id 本身含下划线（oc_ 前缀），用正则提取。"""
    groups = []
    for path in sorted(glob.glob(os.path.join(GROUPS_DIR, "oc_*.md"))):
        fname = os.path.basename(path)[:-3]  # 去掉 .md
        m = re.match(r"^(oc_[0-9a-fA-F]+)_(.+)$", fname)
        if m:
            groups.append((m.group(1), m.group(2)))
    return groups


def run_lark(args):
    try:
        result = subprocess.run([LARK_CLI] + args, capture_output=True, text=True, timeout=30)
        return json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def main():
    state = load_state()
    found = []

    for chat_id, chat_name in load_groups():
        result = run_lark([
            "im", "+chat-messages-list",
            "--chat-id", chat_id, "--as", "bot",
            "--page-size", "10", "--order", "desc",
        ])
        if not result or not result.get("ok"):
            continue

        messages = result.get("data", {}).get("messages", [])
        if not messages:
            continue

        latest_mention = None
        latest_user_msg_id = None

        for msg in messages:
            if msg.get("msg_type") == "system":
                continue
            sender = msg.get("sender", {})
            if sender.get("sender_type") == "app":
                continue

            mid = msg.get("message_id", "")
            if not latest_user_msg_id:
                latest_user_msg_id = mid

            mentions = msg.get("mentions", [])
            mentioned = any(m.get("name") == BOT_NAME for m in mentions)
            content = msg.get("content", "")
            if not mentioned and ("@" + BOT_NAME) not in content:
                continue

            if not latest_mention:
                latest_mention = {
                    "chat_id": chat_id,
                    "chat_name": chat_name,
                    "message_id": mid,
                    "sender": sender.get("name", "unknown"),
                    "content_preview": content[:200].replace("\n", " ").replace("\r", " "),
                }

        if latest_mention and latest_mention["message_id"] != state.get(chat_id, ""):
            found.append(latest_mention)

        if latest_user_msg_id:
            state[chat_id] = latest_user_msg_id

    save_state(state)
    for item in found:
        print(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
