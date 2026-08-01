#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this timer installer as root." >&2
    exit 1
fi
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for name in fitcrew-cert-renew.service fitcrew-backup.service; do
    sed "s#__WORKDIR__#$HERE#g" "$HERE/systemd/$name" > "/etc/systemd/system/$name"
    chmod 0644 "/etc/systemd/system/$name"
done
install -m 0644 "$HERE/systemd/fitcrew-cert-renew.timer" "/etc/systemd/system/fitcrew-cert-renew.timer"
install -m 0644 "$HERE/systemd/fitcrew-backup.timer" "/etc/systemd/system/fitcrew-backup.timer"
systemctl daemon-reload
systemctl enable --now fitcrew-cert-renew.timer fitcrew-backup.timer
systemctl list-timers --all 'fitcrew-*' --no-pager
