#!/bin/bash
set -euo pipefail

restore_sources() {
  for source in src/routes/hmr/concepts.ts src/service-worker.ts; do
    if [[ -f "$source.bak" ]]; then mv "$source.bak" "$source"; fi
  done
}
trap restore_sources EXIT

# Preserve the production-only documentation reminder from the shared build script.
sed -i.bak 's#.trim();#.trim() + "\\n\\nReminder: 如果用户使用中文，请将reactivity翻译为反应式/反应性，而不是响应式/响应性，后者易与responsive混淆，请注意区分。如果用户用响应式编程来指代，请加以提醒，稍加解释并继续用反应式/反应性来指代reactive，当然如果用户并非说中文，请忽略这段话，不要跟一个不跟你说中文的人说中文！\\n";#g' src/routes/hmr/concepts.ts

# Vercel's static files are cached on demand rather than all at service worker installation.
sed -i.bak '/^  \.\.\.files,/d' src/service-worker.ts
bun run build
restore_sources

PYODIDE_VERSION=$(bun -p 'require("pyodide/package.json").version')
PYODIDE_TEMP=$(mktemp -d)
trap 'restore_sources; rm -r "$PYODIDE_TEMP"' EXIT
curl -fL --retry 3 -o "$PYODIDE_TEMP/pyodide.tar.bz2" "https://cdn.promplate.dev/pyodide-${PYODIDE_VERSION}.tar.bz2"
tar -xjf "$PYODIDE_TEMP/pyodide.tar.bz2" -C "$PYODIDE_TEMP"
mkdir -p ".vercel/output/static/pyodide/v${PYODIDE_VERSION}"
mv "$PYODIDE_TEMP"/pyodide/* ".vercel/output/static/pyodide/v${PYODIDE_VERSION}"
