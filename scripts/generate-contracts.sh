#!/usr/bin/env bash
# Generate contracts/meritum.schema.json and contracts/meritum.ts from the
# src/meritum_core/checks/contracts/ package. The only place they are generated;
# consumers (design system, TypeScript apps) copy them, never edit them.
#   scripts/generate-contracts.sh           write the files
#   scripts/generate-contracts.sh --check   fail if the committed files are stale (CI)
# The banner still names checks/contracts.py: changing it would change meritum.ts,
# so it moves with the next contract change that regenerates the file.
# Versions are pinned: pydantic through uv.lock, the TS generator below.
set -euo pipefail
cd "$(dirname "$0")/.."
out=contracts
if [ "${1:-}" = --check ]; then out=$(mktemp -d); fi
uv run --locked python scripts/export_contracts.py "$out/meritum.schema.json"
npx --yes json-schema-to-typescript@15.0.4 -i "$out/meritum.schema.json" -o "$out/meritum.ts" \
  --unreachableDefinitions --additionalProperties false \
  --bannerComment '/* Generated from meritum-core src/meritum_core/checks/contracts.py by scripts/generate-contracts.sh. Do not edit. */'
if [ "$out" != contracts ]; then
  for f in meritum.schema.json meritum.ts; do
    diff -u "contracts/$f" "$out/$f" || { echo "::error file=contracts/$f::stale, run scripts/generate-contracts.sh"; exit 1; }
  done
  echo "contracts up to date"
fi
