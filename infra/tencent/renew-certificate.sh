#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$HERE/runtime/.env.runtime"
COMPOSE="docker compose --env-file $ENV_FILE -f $HERE/compose.yaml"

$COMPOSE --profile operations run --rm certbot renew --quiet --preferred-profile shortlived \
    --webroot --webroot-path /var/www/acme
"$HERE/sync-certificate.sh"
$COMPOSE exec -T caddy caddy reload --config /etc/caddy/Caddyfile
echo '{"operation":"certificate_renewal","result":"complete"}'
