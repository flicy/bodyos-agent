#!/bin/sh
set -eu

python /app/scripts/render_hermes_profile.py --profile-dir /home/bodyos/.hermes/profiles/bodyos
exec hermes --profile bodyos gateway --accept-hooks run
