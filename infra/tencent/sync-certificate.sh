#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$HERE/runtime/.env.runtime"
COMPOSE="docker compose --env-file $ENV_FILE -f $HERE/compose.yaml"

chown 1000:1000 "$HERE/runtime/tls"
chmod 700 "$HERE/runtime/tls"
$COMPOSE --profile operations run --rm --entrypoint /bin/sh certbot -c '
set -eu
source_dir="/etc/letsencrypt/live/$FITCREW_PUBLIC_HOST"
test -f "$source_dir/fullchain.pem"
test -f "$source_dir/privkey.pem"
install -o 1000 -g 1000 -m 0644 "$source_dir/fullchain.pem" /export/fullchain.pem
install -o 1000 -g 1000 -m 0600 "$source_dir/privkey.pem" /export/privkey.pem
'
