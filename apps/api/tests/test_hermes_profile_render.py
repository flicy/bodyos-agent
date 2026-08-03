import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[3]


def test_renderer_builds_a_complete_fail_closed_bodyos_profile(tmp_path: Path) -> None:
    profile = tmp_path / "bodyos-profile"
    environment = {
        **os.environ,
        "BODYOS_MODEL_BASE_URL": "https://bodyos.example.test/v1",
        "FEISHU_ALLOWED_GROUP_ID": "oc_bodyos_group",
    }

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/render_hermes_profile.py"),
            "--app-root",
            str(ROOT),
            "--profile-dir",
            str(profile),
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert (profile / "AGENTS.md").read_text() == (ROOT / "agent/AGENTS.md").read_text()
    assert (profile / "hooks/bodyos-envelope/handler.py").is_file()
    assert (profile / "plugins/bodyos_guard/__init__.py").is_file()

    config = yaml.safe_load((profile / "config.yaml").read_text())
    assert config["model"]["base_url"] == "https://bodyos.example.test/v1"
    assert config["plugins"]["enabled"] == ["bodyos_guard"]
    assert config["hooks_auto_accept"] is True
    assert config["group_sessions_per_user"] is True
    assert config["platforms"]["feishu"]["extra"]["group_rules"] == {
        "oc_bodyos_group": {"policy": "open", "require_mention": True}
    }
