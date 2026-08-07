#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$HERE/runtime/.env.runtime"
PUBLIC_HOST=$(awk -F= '$1 == "FITCREW_PUBLIC_HOST" {print $2}' "$ENV_FILE")
source_dir="$HERE/runtime/letsencrypt/live/$PUBLIC_HOST"

chown 1000:1000 "$HERE/runtime/tls"
chmod 700 "$HERE/runtime/tls"
test -f "$source_dir/fullchain.pem"
test -f "$source_dir/privkey.pem"
install -o 1000 -g 1000 -m 0644 "$source_dir/fullchain.pem" "$HERE/runtime/tls/fullchain.pem"
install -o 1000 -g 1000 -m 0600 "$source_dir/privkey.pem" "$HERE/runtime/tls/privkey.pem"
