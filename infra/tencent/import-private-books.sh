#!/bin/sh
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE="$HERE/runtime/.env.runtime"
OWNER_FILE="$HERE/runtime/owner/owner-bootstrap.json"
COMPOSE="docker compose --env-file $ENV_FILE -f $HERE/compose.yaml"

test -s "$OWNER_FILE"
OWNER_ID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["fitcrew_user_id"])' "$OWNER_FILE")
case "$OWNER_ID" in
    ????????-????-4???-[89ab]???-????????????) ;;
    *) echo "Owner identity record is invalid." >&2; exit 1 ;;
esac

for name in glucose-revolution.pdf sleep-guide.pdf longevity-handbook.pdf; do
    test -s "$HERE/runtime/private-books/$name"
done
chown 1000:1000 "$HERE/runtime/private-books" "$HERE/runtime/private-books"/*.pdf
chmod 700 "$HERE/runtime/private-books"
chmod 600 "$HERE/runtime/private-books"/*.pdf

$COMPOSE exec -T api python /app/scripts/import_private_books.py \
    /private-books/glucose-revolution.pdf --user-id "$OWNER_ID" --title "控糖革命" \
    --author "Jessie Inchauspé"
$COMPOSE exec -T api python /app/scripts/import_private_books.py \
    /private-books/sleep-guide.pdf --user-id "$OWNER_ID" \
    --title "睡眠优化完全指南：科学与实践"
$COMPOSE exec -T api python /app/scripts/import_private_books.py \
    /private-books/longevity-handbook.pdf --user-id "$OWNER_ID" --title "百岁人生行动手册"
echo "Three owner-only sources imported; PDF files remain outside Git."
