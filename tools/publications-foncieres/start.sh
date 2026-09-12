#!/usr/bin/env bash
# One command to set everything up (first run) and capture (every run).
#   ./start.sh
# Any extra argument is passed straight to capture.py, e.g.
#   ./start.sh --no-filter
set -euo pipefail
cd "$(dirname "$0")"

PY=venv/bin/python

if [ ! -x "$PY" ]; then
  echo "==> Installation (une seule fois)"
  python3 -m venv venv
  venv/bin/pip install --quiet --upgrade pip
  venv/bin/pip install --quiet -r requirements.txt
fi

# Playwright needs a browser it can drive. Prefer one already on the machine
# over a 150 MB download; .browser-ok records that this is settled.
if [ ! -f venv/.browser-ok ] && [ -z "${PF_CHROMIUM:-}" ]; then
  echo "==> Recherche d'un navigateur utilisable"
  for candidate in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "$(command -v google-chrome || true)" \
    "$(command -v chromium || true)" \
    "$(command -v chromium-browser || true)"
  do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      export PF_CHROMIUM="$candidate"
      echo "    trouvé: $candidate"
      break
    fi
  done

  if [ -z "${PF_CHROMIUM:-}" ]; then
    echo "    aucun navigateur local, téléchargement via Playwright"
    venv/bin/playwright install chromium
    touch venv/.browser-ok
  fi
fi

echo
exec "$PY" capture.py "$@"
