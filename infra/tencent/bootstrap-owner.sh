#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$HERE/runtime/.env.runtime"
COMPOSE="docker compose --env-file $ENV_FILE -f $HERE/compose.yaml"

$COMPOSE exec -T api python /app/scripts/bootstrap_owner.py
test -s "$HERE/runtime/owner/owner-bootstrap.json"
test -s "$HERE/runtime/owner/owner-pairing.png"
echo "Pairing artifact is ready in the private owner runtime directory."
