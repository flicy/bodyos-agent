#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$HERE/runtime/.env.runtime"
COMPOSE="docker compose --env-file $ENV_FILE -f $HERE/compose.yaml"

echo "Preparing private model credential volumes for the non-root BodyOS runtime."
$COMPOSE run --rm --user 0:0 --cap-add CHOWN --cap-add FOWNER \
    --entrypoint /bin/sh api -c '
set -eu
chmod 700 /home/bodyos/.codex /home/bodyos/.hermes
chown -R 10001:10001 /home/bodyos/.codex /home/bodyos/.hermes
'
echo "Codex primary OAuth login (one-time device confirmation):"
$COMPOSE run --rm api codex login --device-auth
echo "Hermes fallback OAuth login (one-time device confirmation):"
$COMPOSE run --rm api hermes auth add openai-codex
echo "Model credentials are stored in Docker volumes, never in Git or the runtime env file."
