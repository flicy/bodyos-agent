#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$HERE/runtime/.env.runtime"
COMPOSE="docker compose --env-file $ENV_FILE -f $HERE/compose.yaml"

echo "Codex primary OAuth login (one-time device confirmation):"
$COMPOSE run --rm api codex login --device-auth
echo "Hermes fallback OAuth login (one-time device confirmation):"
$COMPOSE run --rm api hermes login openai-codex
echo "Model credentials are stored in Docker volumes, never in Git or the runtime env file."
