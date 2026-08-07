# FitCrew / BodyOS V2 Owner-only Alpha Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship, test, submit through PR, and deploy an owner-only FitCrew V2 Alpha that connects private HealthKit/Yuwell data and private book knowledge to BodyOS without allowing raw health data into group or model scopes.

**Architecture:** A small FastAPI service and worker run with PostgreSQL on the existing Tencent Lighthouse. An iOS HealthKit Bridge uploads idempotent encrypted batches. BodyOS reaches data only through a scope-enforcing tool API, while Motclaw uses Codex Harness first and Hermes on demand. Private book chunks are encrypted and searched in-process for the owner-only Alpha.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, Alembic, cryptography/AES-GCM, pytest, Swift/SwiftUI/HealthKit, XcodeGen, Docker Compose, Caddy, GitHub Actions.

---

## File map

- `apps/api/bodyos_api/`: HTTP API, configuration, database, policy, encryption, health, knowledge, memory, BodyOS, and model routing.
- `apps/api/tests/`: unit and integration tests using isolated SQLite and fake providers.
- `apps/worker/bodyos_worker/`: retention, feature calculation, outbox, backup checks, and study checkpoints.
- `apps/ios-bridge/`: SwiftUI HealthKit Bridge, secure device binding, incremental sync, and tests.
- `packages/contracts/`: versioned JSON Schemas shared by iOS, API, Agent tools, and tests.
- `agent/`: BodyOS runtime rules and scoped-tool contract.
- `scripts/`: safe installer, book importer, BodyOS tool CLI, deployment and evidence scripts.
- `infra/tencent/`: Docker Compose, container definitions, reverse proxy, example environment, backup and rollback scripts.
- `.github/`: CI, PR template, ownership, and dependency/security policy.
- `docs/`: bilingual product, privacy, deployment, runbook, evidence, and study documents.

### Task 1: Lock the approved contract and repository safety

**Files:**
- Create: `docs/superpowers/specs/2026-08-01-fitcrew-v2-owner-alpha-design.md`
- Create: `docs/superpowers/plans/2026-08-01-fitcrew-v2-owner-alpha.md`
- Modify: `.gitignore`

- [ ] **Step 1: Verify the isolated baseline**

Run: `bash -n install.sh scripts/add-group.sh && python3 -m json.tool cron/jobs.seed.json >/dev/null`

Expected: exit 0 from remote `main` at `c5263b3`.

- [ ] **Step 2: Add private-artifact exclusions**

Append exact exclusions for `.env*`, `data/`, `backups/`, `evidence/private/`, `*.sqlite*`, `*.pdf`, Xcode user data, and generated health exports.

- [ ] **Step 3: Scan the design and plan for bilingual coverage and unresolved markers**

Run: `python3 -c 'from pathlib import Path; m=["T"+"BD","TO"+"DO","implement "+"later","fill "+"in"]; assert not any(x in p.read_text() for p in Path("docs/superpowers").rglob("*.md") for x in m)'`

Expected: no unresolved placeholder.

- [ ] **Step 4: Commit the approved contract**

Run: `git add docs/superpowers .gitignore && git commit -m "docs: lock V2 owner alpha design"`

Expected: one documentation commit containing no private data.

### Task 2: Bootstrap the tested API and schema

**Files:**
- Create: `pyproject.toml`
- Create: `apps/api/bodyos_api/{__init__,app,config,db,models,schemas}.py`
- Create: `apps/api/tests/{conftest,test_healthcheck,test_schema}.py`
- Create: `packages/contracts/health-sync-v1.schema.json`
- Create: `alembic.ini`, `apps/api/migrations/env.py`, `apps/api/migrations/versions/0001_owner_alpha.py`

- [ ] **Step 1: Write failing API and schema tests**

The tests require `GET /healthz` to return `{"status":"ok","version":"v2.0.0-alpha.1"}` and validate a sync batch containing `batch_id`, device binding, consent, source, timestamps, unit, and samples.

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -m pytest apps/api/tests/test_healthcheck.py apps/api/tests/test_schema.py -q`

Expected: collection fails because `bodyos_api` and the contract do not exist.

- [ ] **Step 3: Implement the minimum application and models**

Create focused tables for users, identities, device bindings, consents, sync batches, encrypted health samples, daily features, insights, memories, knowledge sources/chunks/reviews, demand items, audit events, and outbox records. Add unique constraints for identity bindings and sample idempotency.

- [ ] **Step 4: Run GREEN and migration checks**

Run: `python -m pytest apps/api/tests/test_healthcheck.py apps/api/tests/test_schema.py -q && alembic upgrade head`

Expected: all tests pass and the migration applies to an isolated test database.

- [ ] **Step 5: Commit**

Run: `git add pyproject.toml apps packages alembic.ini && git commit -m "feat: add owner alpha API foundation"`

### Task 3: Enforce encryption, consent, scopes, and DLP

**Files:**
- Create: `apps/api/bodyos_api/{crypto,consent,policy,dlp,audit}.py`
- Create: `apps/api/tests/{test_crypto,test_consent,test_policy,test_dlp}.py`

- [ ] **Step 1: Write failing security tests**

Cover AES-GCM round trips and tamper rejection; category/purpose consent; immediate withdrawal; group-to-health/private/private-knowledge denial; fixed behavior tokens; and DLP rejection of glucose, HRV, sleep, weight, medication, routes, and identifiers.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest apps/api/tests/test_crypto.py apps/api/tests/test_consent.py apps/api/tests/test_policy.py apps/api/tests/test_dlp.py -q`

Expected: failures because the security modules do not exist.

- [ ] **Step 3: Implement minimal deterministic controls**

Use AES-GCM with a versioned environment key; explicit enums for scope, purpose, category, and behavior token; deny-by-default authorization; structured audit events without content; and a group outbox that accepts only token IDs and user-confirmed state.

- [ ] **Step 4: Verify GREEN**

Run: `python -m pytest apps/api/tests/test_crypto.py apps/api/tests/test_consent.py apps/api/tests/test_policy.py apps/api/tests/test_dlp.py -q`

Expected: all security tests pass.

- [ ] **Step 5: Commit**

Run: `git add apps/api && git commit -m "feat: enforce consent scopes and output DLP"`

### Task 4: Ingest health batches and compute deterministic features

**Files:**
- Create: `apps/api/bodyos_api/{health_routes,health_service,features}.py`
- Create: `apps/api/tests/{test_health_ingest,test_features,test_health_export_delete}.py`
- Create: `apps/worker/bodyos_worker/{__init__,retention,study}.py`

- [ ] **Step 1: Write failing ingestion tests**

Cover valid authorized ingest, missing consent, wrong user binding, duplicate batch replay, duplicate sample UUID, mg/dL/mmol/L conversion, timezone preservation, and encrypted-at-rest values.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest apps/api/tests/test_health_ingest.py apps/api/tests/test_features.py apps/api/tests/test_health_export_delete.py -q`

Expected: failures because health routes and services do not exist.

- [ ] **Step 3: Implement the minimum sync and feature pipeline**

Expose bind, consent, sync, status, feature, export, withdrawal, and deletion endpoints. Compute daily quality, glucose summary/windows, overnight stability, sleep, HRV, resting-heart-rate, workout, and activity features without sending raw samples to a model.

- [ ] **Step 4: Add retention and study checkpoints**

Implement 30-day raw expiry, 13-month authorized aggregate expiry, and day 3/8/15/16 study jobs. Day 16 performs an idempotent full-sync reconciliation request rather than inventing results.

- [ ] **Step 5: Verify GREEN and commit**

Run: `python -m pytest apps/api/tests/test_health_ingest.py apps/api/tests/test_features.py apps/api/tests/test_health_export_delete.py -q`

Expected: all health tests pass.

Run: `git add apps && git commit -m "feat: add encrypted HealthKit ingestion and features"`

### Task 5: Build private knowledge and reviewed demand pools

**Files:**
- Create: `apps/api/bodyos_api/{knowledge,knowledge_routes,demand}.py`
- Create: `apps/api/tests/{test_knowledge,test_demand}.py`
- Create: `scripts/import_private_books.py`
- Create: `docs/knowledge/private-book-register.example.json`

- [ ] **Step 1: Write failing knowledge and demand tests**

Require encrypted private chunks, page citations, owner-only retrieval, published-only public retrieval, review-state transitions, source withdrawal behavior, and demand-state transitions.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest apps/api/tests/test_knowledge.py apps/api/tests/test_demand.py -q`

Expected: failures because the services do not exist.

- [ ] **Step 3: Implement ingestion and lexical retrieval**

Extract page text with `pypdf`, hash the original file, normalize and chunk text with page metadata, encrypt chunk text, and score decrypted owner-only chunks in-process. Do not copy PDF files into the repository or container image.

- [ ] **Step 4: Implement review and demand APIs**

Enforce the approved candidate and demand state machines with provenance, reviewer, rationale, applicability, and immutable version fields.

- [ ] **Step 5: Verify GREEN and commit**

Run: `python -m pytest apps/api/tests/test_knowledge.py apps/api/tests/test_demand.py -q`

Expected: all tests pass.

Run: `git add apps scripts docs/knowledge && git commit -m "feat: add private knowledge and reviewed demand pools"`

### Task 6: Build the HealthKit Bridge

**Files:**
- Create: `apps/ios-bridge/project.yml`
- Create: `apps/ios-bridge/FitCrewHealthBridge/{App,ContentView,HealthKitClient,SyncClient,KeychainStore,ConsentStore}.swift`
- Create: `apps/ios-bridge/FitCrewHealthBridgeTests/{BatchTests,CursorTests,UnitTests}.swift`
- Create: `apps/ios-bridge/FitCrewHealthBridge/Info.plist`

- [ ] **Step 1: Write failing Swift tests**

Require stable batch IDs, cursor advancement only after success, blood-glucose unit normalization, retry-safe payloads, and no access to unrelated HealthKit types.

- [ ] **Step 2: Verify RED in GitHub-compatible form**

Run: `swift test --package-path apps/ios-bridge/Core`

Expected: failure because the core package does not exist.

- [ ] **Step 3: Implement a testable core and SwiftUI app**

The core converts HealthKit results into the versioned JSON contract. The app requests explicit read authorization, stores device credentials in Keychain, performs observer/incremental sync, shows last sync and quality, and exposes a full-reconciliation action.

- [ ] **Step 4: Build and test**

Run locally when full Xcode is available, otherwise run the same commands in macOS GitHub Actions:

`xcodegen generate --spec apps/ios-bridge/project.yml && xcodebuild -project apps/ios-bridge/FitCrewHealthBridge.xcodeproj -scheme FitCrewHealthBridge -sdk iphonesimulator build test CODE_SIGNING_ALLOWED=NO`

Expected: build and tests exit 0.

- [ ] **Step 5: Commit**

Run: `git add apps/ios-bridge packages/contracts && git commit -m "feat: add owner HealthKit bridge"`

### Task 7: Connect BodyOS, Feishu, and model routing

**Files:**
- Create: `apps/api/bodyos_api/{bodyos_routes,model_gateway}.py`
- Create: `apps/api/tests/{test_bodyos,test_model_gateway}.py`
- Create: `scripts/bodyos_tool.py`
- Modify: `agent/AGENTS.md`, `agent/HERMES.md`, `cron/jobs.seed.json`, `config/config.template.yaml`, `config/env.template`
- Modify: `scripts/feishu_group_watcher.py`, `install.sh`, `scripts/add-group.sh`

- [ ] **Step 1: Write failing BodyOS and routing tests**

Cover DM feature/knowledge retrieval, group behavior tokens, group health denial, de-identified model packages, primary success, timeout and bounded retry, Hermes fallback, both-provider fail-closed behavior, and restart-persistent queued work.

- [ ] **Step 2: Write regression tests for V1 bugs**

Reproduce duplicate mention replies, installer rerun duplication, invalid group themes, unsafe default-open configuration, and visible secret prompts.

- [ ] **Step 3: Verify RED**

Run: `python -m pytest apps/api/tests/test_bodyos.py apps/api/tests/test_model_gateway.py tests/test_v1_regressions.py -q`

Expected: failures for missing routes and existing V1 defects.

- [ ] **Step 4: Implement the scoped tool and model gateway**

BodyOS receives only authorized tool results. Group output uses fixed tokens. The model gateway records provider, bounded feature names, latency, status, and error class without content. Primary Codex Harness and on-demand Hermes adapters are configurable commands; no paid API key fallback exists.

- [ ] **Step 5: Fix V1 regressions and verify GREEN**

Run: `python -m pytest apps/api/tests/test_bodyos.py apps/api/tests/test_model_gateway.py tests/test_v1_regressions.py -q && bash -n install.sh scripts/add-group.sh`

Expected: all tests and shell syntax pass.

- [ ] **Step 6: Commit**

Run: `git add apps agent config cron install.sh scripts tests && git commit -m "feat: connect scoped BodyOS and stable model routing"`

### Task 8: Package deployment, backup, and operations

**Files:**
- Create: `infra/tencent/{compose.yaml,Dockerfile.api,Dockerfile.worker,Caddyfile,env.example,deploy.sh,backup.sh,restore-test.sh,rollback.sh}`
- Create: `docs/operations/deployment-and-rollback.md`
- Create: `docs/privacy/data-processing-and-retention.md`
- Create: `docs/experiments/owner-cgm-16-day-runbook.md`
- Create: `apps/api/tests/test_no_sensitive_logs.py`

- [ ] **Step 1: Write failing operations checks**

Require non-root containers, health checks, resource limits, read-only mounts where possible, no paid service references, no secrets in examples, content-free logs, backup encryption, and explicit rollback SHA.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest apps/api/tests/test_no_sensitive_logs.py -q && docker compose -f infra/tencent/compose.yaml config`

Expected: failure until the deployment files exist; if local Docker is unavailable, run Compose validation on CI/server.

- [ ] **Step 3: Implement deployment and bilingual runbooks**

Use pinned images, local PostgreSQL, Caddy or an owner-only secure ingress, encrypted backups, migration-before-start, health-gated cutover, and rollback to the previous immutable SHA.

- [ ] **Step 4: Verify and commit**

Run: `python -m pytest apps/api/tests/test_no_sensitive_logs.py -q`

Expected: pass.

Run: `git add infra docs apps/api/tests && git commit -m "ops: add zero-cost Tencent deployment and rollback"`

### Task 9: Add CI, review, release, and website truthfulness

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.github/CODEOWNERS`
- Create: `SECURITY.md`, `LICENSE`
- Modify: `README.md`, `CHANGELOG.md`, `landing/index.html`

- [ ] **Step 1: Add CI that reproduces local verification**

Run Python tests, Ruff, JSON/YAML checks, ShellCheck, secret scan, Compose config, Swift core tests, and iOS simulator build. Upload only non-sensitive summaries.

- [ ] **Step 2: Update public documentation**

Document V2 Alpha truthfully, replace broken links, identify Owner-only status, explain HealthKit optionality, and state that private health data and books are never committed.

- [ ] **Step 3: Run the full local verification suite**

Run: `python -m pytest -q && ruff check . && bash -n install.sh scripts/*.sh && python -m json.tool cron/jobs.seed.json >/dev/null`

Expected: all checks exit 0.

- [ ] **Step 4: Commit and push**

Run: `git add .github README.md CHANGELOG.md SECURITY.md LICENSE landing && git commit -m "chore: add V2 CI governance and release docs" && git push -u origin codex/v2-owner-alpha`

Expected: the remote branch exists with no secrets or private files.

- [ ] **Step 5: Create the PR**

Run: `gh pr create --repo flicy/fitcrew-agent --base main --head codex/v2-owner-alpha --title "feat: ship FitCrew V2 owner-only alpha" --body-file <generated-pr-body>`

Expected: a PR URL with scope, tests, deployment, privacy, rollback, and open physical checkpoints.

### Task 10: Deploy and produce fresh evidence

**Files:**
- Create: `docs/evidence/2026-08-01-owner-alpha-verification.md`

- [ ] **Step 1: Inventory the server without mutation**

Record OS, CPU, memory, disk, ports, container runtime, existing services, TLS route, backup location, and rollback target without recording secrets or public IPs in Git.

- [ ] **Step 2: Deploy the tested PR SHA**

Build or pull pinned images, create `0600` secrets on the host, run migrations, start the stack, and require passing health checks before routing any BodyOS test traffic.

- [ ] **Step 3: Import all three private books outside Git**

Run the importer over the three confirmed desktop PDFs, send encrypted chunks to the owner knowledge store, and retain only redacted counts/hashes in evidence.

- [ ] **Step 4: Run synthetic security E2E**

Verify cross-group canaries, group `403`, withdrawal, DLP, wrong identity, log redaction, export, deletion, backup, restore, and rollback.

- [ ] **Step 5: Run bounded live E2E**

Use only the designated BodyOS owner DM and test group. Validate a DM knowledge answer with page citations, a confirmed group behavior token with no health data, the primary model route, the injected fallback route, and restart recovery.

- [ ] **Step 6: Run the first real HealthKit/Yuwell batch**

On the owner iPhone, authorize the minimum data types, bind the device, upload one real batch, and verify only redacted record count, source, time window, unit/timezone quality, and sync status. Start day 3/8/15/16 checkpoints.

- [ ] **Step 7: Run final verification and update PR**

Run the complete test/build suite again, inspect Git diff and secret scan, check cloud health, and update the PR/evidence with exact SHA, CI URL, deployment version, redacted E2E results, risks, and rollback.

Expected: every same-day acceptance item is either evidenced as complete or named as an external physical/account blocker with one minimal user action. No day-16 outcome is claimed early.
