#!/usr/bin/env python3
"""
FitCrew 需求池 → 飞书需求采集文档 同步脚本

把「需求池」多维表格里的需求，渲染成可读的飞书文档（05-需求采集），
由团队统一管理。配合 cron 定期运行，即可实现"需求自动沉淀成飞书文档"。

依赖：lark-cli 已登录，且具备 base:record:retrieve（读需求池）与
     markdown 文档写权限。

用法：
    python3 sync_requirements_to_doc.py
"""
import datetime
import json
import subprocess
import sys

# ---- 配置 ----
BASE_TOKEN = "O54Ub21F9aLZ1osVV3tcgy1qnIe"          # 需求池多维表格
TABLE_ID = "tblCPCvLz22LwjuT"                        # 需求表
DOC_FILE_TOKEN = "M7gpbkMXWoYP6Xx8qBlccC2dnlg"       # 05-需求采集 飞书文档
SURVEY_URL = "https://my.feishu.cn/share/base/shrcn09DqqE2jjV5mWi7ZPrrG8f"
POOL_URL = "https://my.feishu.cn/base/O54Ub21F9aLZ1osVV3tcgy1qnIe"
LOCAL_MD = "/tmp/fitcrew_requirements_doc.md"


def lark(args):
    """Run a lark-cli command, return parsed JSON (or None on error)."""
    cmd = ["lark-cli"] + args + ["--as", "user", "--json"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
        i = out.find("{")
        return json.loads(out[i:]) if i >= 0 else None
    except Exception as e:
        print(f"  [warn] lark-cli error: {e}", file=sys.stderr)
        return None


def text_of(v):
    """Normalize a Bitable field value to plain text."""
    if v is None:
        return ""
    if isinstance(v, list):
        parts = []
        for x in v:
            if isinstance(x, dict):
                parts.append(x.get("text") or x.get("name") or "")
            else:
                parts.append(str(x))
        return " ".join(p for p in parts if p)
    if isinstance(v, dict):
        return v.get("text") or v.get("name") or json.dumps(v, ensure_ascii=False)
    return str(v)


def fetch_records():
    url = f"/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{TABLE_ID}/records"
    resp = lark(["api", "GET", url, "--params", '{"page_size":100}'])
    if not resp or not resp.get("ok"):
        err = (resp or {}).get("error", {})
        print(f"  [error] 读取需求池失败: {err.get('message', resp)}", file=sys.stderr)
        return None
    return resp.get("data", {}).get("items", [])


def render(records):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("# FitCrew · 需求采集文档\n")
    lines.append("> 所有通过落地页问卷提交的需求，都会沉淀到这里，由团队统一 review、排期、跟进。")
    lines.append("> 本文档由 Cola 通过飞书 CLI 自动同步（需求池 → 本文档）。")
    lines.append(f"> 最后同步：{now}\n")
    lines.append("---\n")
    lines.append("## 需求从哪里来\n")
    lines.append(f"- 🌐 落地页问卷：{SURVEY_URL}")
    lines.append(f"- 🗂️ 需求池（多维表格）：{POOL_URL}\n")
    lines.append("## 需求列表\n")
    if not records:
        lines.append("> 暂无需求，等待第一条需求。\n")
    else:
        lines.append("| 状态 | 优先级 | 需求描述 | 来源 | 提交人 |")
        lines.append("|---|---|---|---|---|")
        for r in records:
            f = r.get("fields", {})
            status = text_of(f.get("状态")) or "待评审"
            prio = text_of(f.get("优先级")) or "-"
            desc = text_of(f.get("需求描述")) or "(无描述)"
            source = text_of(f.get("来源")) or "落地页问卷"
            who = text_of(f.get("你的称呼")) or text_of(f.get("飞书账号")) or "-"
            # escape pipes / newlines for the table cell
            desc = desc.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {status} | {prio} | {desc} | {source} | {who} |")
        lines.append("")
    lines.append("---\n")
    lines.append(f"*有新需求？填 [落地页问卷]({SURVEY_URL})。*\n")
    return "\n".join(lines)


def main():
    print("读取需求池 …")
    records = fetch_records()
    if records is None:
        print("同步中止（需求池读取失败，可能缺少 base:record:retrieve 权限）。")
        sys.exit(1)
    print(f"  共 {len(records)} 条需求")
    md = render(records)
    with open(LOCAL_MD, "w") as fh:
        fh.write(md)
    print("覆写飞书文档 05-需求采集 …")
    resp = lark(["markdown", "+overwrite", "--file-token", DOC_FILE_TOKEN, "--file", LOCAL_MD])
    if resp and resp.get("ok"):
        print("✅ 同步完成：需求已渲染进飞书文档 05-需求采集")
    else:
        err = (resp or {}).get("error", {})
        print(f"❌ 覆写失败: {err.get('message', resp)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
