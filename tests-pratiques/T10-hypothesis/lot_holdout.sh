#!/usr/bin/env bash
# T10b : rejeu des mutants hors liste, un processus de test a la fois. Variables T10_RACINE et T10_BRUTS requises.
cd "$(dirname "$0")"; export MSYS_NO_PATHCONV=1 PYTHONUTF8=1
for s in wd-5-9 wd-8-4 us-7-14 us-7-15 us-7-16; do for b in C A; do for e in 1 2; do
  [ -s "$T10_BRUTS/holdout-$s-$b$e.json" ] && continue
  uv run python evaluer_holdout.py "$s" "$b" "$e" >> "$T10_BRUTS/lot_holdout.log" 2>&1
done; done; done
echo FINI >> "$T10_BRUTS/lot_holdout.log"
