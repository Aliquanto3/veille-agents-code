#!/usr/bin/env bash
# T10b : evalue les executions C une a une (un seul processus de test a la fois). Variables T10_RACINE et T10_BRUTS requises.
cd "$(dirname "$0")"; export MSYS_NO_PATHCONV=1 PYTHONUTF8=1
for it in $1; do
  s="${it%%:*}"; e="${it##*:}"
  [ -s "$T10_BRUTS/eval-$s-C$e.json" ] && continue
  uv run python evaluer.py "$s" C "$e" >> "$T10_BRUTS/lot_eval.log" 2>&1
done
echo FINI >> "$T10_BRUTS/lot_eval.log"
