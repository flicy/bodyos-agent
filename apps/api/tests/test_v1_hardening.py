import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[3]


def test_default_group_policy_is_allowlist_and_global_user_access_is_closed() -> None:
    config = yaml.safe_load((ROOT / "config/config.template.yaml").read_text())
    env_template = (ROOT / "config/env.template").read_text()

    assert config["platforms"]["feishu"]["extra"]["default_group_policy"] == "allowlist"
    assert "FEISHU_ALLOW_ALL_USERS=false" in env_template
    assert "GATEWAY_ALLOW_ALL_USERS=false" in env_template


def test_installer_uses_hidden_secret_input_and_no_paid_model_api_prompt() -> None:
    installer = (ROOT / "install.sh").read_text()

    assert "read -r -s" in installer
    assert "FITCREW_API_KEY" not in installer
    assert "deepseek" not in installer.casefold()
    assert "bodyos_guard" in installer


def test_gateway_image_installs_the_feishu_transport_extra() -> None:
    dockerfile = (ROOT / "infra/tencent/Dockerfile.api").read_text()

    assert '"hermes-agent[feishu]==${HERMES_VERSION}"' in dockerfile


def test_group_watcher_has_idempotency_and_never_emits_message_preview() -> None:
    watcher = (ROOT / "scripts/feishu_group_watcher.py").read_text()

    assert "--idempotency-key" in watcher
    assert "processed_message_hashes" in watcher
    assert "content_preview" not in watcher


def test_universal_group_watcher_runs_without_an_llm() -> None:
    jobs = json.loads((ROOT / "cron/jobs.seed.json").read_text())["jobs"]

    assert jobs
    assert all(job.get("no_agent") is True for job in jobs)
