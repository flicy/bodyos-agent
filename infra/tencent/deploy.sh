#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../.." && pwd)
RUNTIME="$HERE/runtime"
ENV_FILE="$RUNTIME/.env.runtime"
COMPOSE="docker compose --env-file $ENV_FILE -f $HERE/compose.yaml"

if [ ! -f "$ENV_FILE" ]; then
    echo "Runtime environment missing; collecting owner-only values without echoing secrets."
    (cd "$HERE" && python3 generate-runtime-env.py)
fi

mkdir -p "$RUNTIME/acme" "$RUNTIME/tls" "$RUNTIME/letsencrypt" "$RUNTIME/backups" \
    "$RUNTIME/private-books" "$RUNTIME/owner"
chmod 700 "$RUNTIME" "$RUNTIME/tls" "$RUNTIME/letsencrypt" "$RUNTIME/backups" \
    "$RUNTIME/private-books" "$RUNTIME/owner"
chmod 755 "$RUNTIME/acme"
chown 10001:10001 "$RUNTIME/private-books" "$RUNTIME/owner"
install -m 0644 "$HERE/Caddyfile.http" "$RUNTIME/Caddyfile"

DEPLOY_SHA=$(git -C "$ROOT" rev-parse HEAD)
case "$DEPLOY_SHA" in
    *[!0-9a-f]*|'') echo "Invalid deploy SHA" >&2; exit 1 ;;
esac

echo "Building immutable BodyOS image for ${DEPLOY_SHA}."
FITCREW_IMAGE_TAG="$DEPLOY_SHA" $COMPOSE build api
python3 "$HERE/set-runtime-image.py" --file "$ENV_FILE" "$DEPLOY_SHA"

echo "Starting database, API, worker, Feishu gateway, and HTTP certificate endpoint."
$COMPOSE up -d db api worker gateway caddy

attempt=0
until $COMPOSE exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then
        echo "API health gate failed; previous image can be restored with rollback.sh." >&2
        exit 1
    fi
    sleep 2
done

PUBLIC_HOST=$(awk -F= '$1 == "FITCREW_PUBLIC_HOST" {print $2}' "$ENV_FILE")
python3 -c 'import ipaddress,sys; ipaddress.ip_address(sys.argv[1])' "$PUBLIC_HOST"
if [ ! -f "$RUNTIME/letsencrypt/live/$PUBLIC_HOST/fullchain.pem" ]; then
    ACME_EMAIL=$(awk -F= '$1 == "FITCREW_ACME_EMAIL" {print substr($0, index($0, "=") + 1)}' "$ENV_FILE")
    if [ -n "$ACME_EMAIL" ]; then
        $COMPOSE --profile operations run --rm certbot certonly --non-interactive --agree-tos \
            --email "$ACME_EMAIL" --preferred-profile shortlived --webroot \
            --webroot-path /var/www/acme --ip-address "$PUBLIC_HOST"
    else
        $COMPOSE --profile operations run --rm certbot certonly --non-interactive --agree-tos \
            --register-unsafely-without-email --preferred-profile shortlived --webroot \
            --webroot-path /var/www/acme --ip-address "$PUBLIC_HOST"
    fi
fi

"$HERE/sync-certificate.sh"
install -m 0644 "$HERE/Caddyfile.https" "$RUNTIME/Caddyfile"
$COMPOSE restart caddy

echo "BodyOS deployed at SHA ${DEPLOY_SHA}; secrets and private data were not printed."
echo "Next: run model-login.sh once, then verify https://${PUBLIC_HOST}/healthz."
