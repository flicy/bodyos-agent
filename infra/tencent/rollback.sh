#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$HERE/runtime/.env.runtime"
COMPOSE="docker compose --env-file $ENV_FILE -f $HERE/compose.yaml"
ROLLBACK_SHA=${ROLLBACK_SHA:-${1:-}}

case "$ROLLBACK_SHA" in
    [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
    *) echo "ROLLBACK_SHA must be a full 40-character hexadecimal commit SHA." >&2; exit 1 ;;
esac

docker image inspect "fitcrew-bodyos:$ROLLBACK_SHA" >/dev/null
"$HERE/backup.sh"
FITCREW_IMAGE_TAG="$ROLLBACK_SHA" $COMPOSE up -d --no-build api worker gateway
python3 "$HERE/set-runtime-image.py" --file "$ENV_FILE" "$ROLLBACK_SHA"
$COMPOSE exec -T api python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=5)"
echo "Application rollback health gate passed; database backup was taken first."
