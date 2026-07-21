#!/usr/bin/env python3
"""安全地往 profile 的 config.yaml 的 platforms.feishu.extra.group_rules 增加一个群规则。

用 PyYAML 做完整的 load→modify→dump 往返，保证产出的永远是合法 YAML
（避免手工行编辑把 config.yaml 写坏导致 Hermes 静默回退默认配置）。

用法：
  python3 add_group_rule.py <profile_dir> <chat_id> [--require-mention true|false]
"""
import sys, os, shutil, datetime

try:
    import yaml
except ImportError:
    sys.exit("需要 PyYAML：pip install pyyaml")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    profile_dir = sys.argv[1]
    chat_id = sys.argv[2]
    require_mention = False
    if "--require-mention" in sys.argv:
        val = sys.argv[sys.argv.index("--require-mention") + 1].strip().lower()
        require_mention = val in ("true", "1", "yes")

    cfg_path = os.path.join(profile_dir, "config.yaml")
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f) or {}

    # 校验：确保能解析（写坏的配置在这里就会暴露）
    platforms = cfg.setdefault("platforms", {})
    feishu = platforms.setdefault("feishu", {})
    extra = feishu.setdefault("extra", {})
    extra.setdefault("default_group_policy", "open")
    rules = extra.setdefault("group_rules", {}) or {}
    rules[chat_id] = {"policy": "open", "require_mention": require_mention}
    extra["group_rules"] = rules

    # 备份后写回
    bak = cfg_path + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(cfg_path, bak)
    with open(cfg_path, "w") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    # 再次校验写回结果可解析
    with open(cfg_path) as f:
        yaml.safe_load(f)
    print(f"✅ 已为 {chat_id} 写入 group_rule（require_mention={require_mention}）。备份：{bak}")
    print("⚠️ 记得 gateway restart 让配置生效。")


if __name__ == "__main__":
    main()
