from pathlib import Path

ROOT = Path(__file__).parents[3]


def test_tencent_compose_has_owner_alpha_hardening() -> None:
    compose = (ROOT / "infra/tencent/compose.yaml").read_text()

    for service in ("db:", "api:", "worker:", "gateway:", "caddy:"):
        assert service in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "NET_BIND_SERVICE" in compose
    assert "mem_limit:" in compose
    assert "healthcheck:" in compose
    assert '"8000:8000"' not in compose

    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    assert "--wait --wait-timeout 120 db api caddy" in workflow
    assert "curl --fail --silent --show-error http://127.0.0.1/healthz" in workflow


def test_operations_bundle_has_tls_backup_restore_and_sha_rollback() -> None:
    expected = [
        "Dockerfile.api",
        "Caddyfile.http",
        "Caddyfile.https",
        "deploy.sh",
        "backup.sh",
        "restore-test.sh",
        "rollback.sh",
        "renew-certificate.sh",
    ]
    for name in expected:
        assert (ROOT / "infra/tencent" / name).is_file(), name

    rollback = (ROOT / "infra/tencent/rollback.sh").read_text()
    assert "ROLLBACK_SHA" in rollback
    assert "git checkout" not in rollback


def test_examples_do_not_contain_committable_secrets() -> None:
    example = (ROOT / "infra/tencent/env.example").read_text()
    assert "sk-" not in example
    assert "cli_" not in example
    assert "CHANGE_ME" not in example
    assert "BODYOS_ENCRYPTION_KEY=" not in example


def test_alembic_uses_the_production_database_environment() -> None:
    migration_environment = (ROOT / "apps/api/migrations/env.py").read_text()
    assert 'os.environ.get("BODYOS_DATABASE_URL")' in migration_environment
    assert 'config.set_main_option("sqlalchemy.url"' in migration_environment
