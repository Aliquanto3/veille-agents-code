#!/usr/bin/env bash
# T10 : evalue les executions d'agent une a une (un seul processus de test a la fois).
# usage : lot_eval.sh "<story>:<bras><essai> ..."
cd "$(dirname "$0")"; export MSYS_NO_PATHCONV=1 PYTHONUTF8=1
for it in $1; do
  s="${it%%:*}"; be="${it##*:}"; b="${be:0:1}"; e="${be:1}"
  [ -s "resultats-bruts/eval-$s-$b$e.json" ] && continue
  uv run python evaluer.py "$s" "$b" "$e" >> resultats-bruts/lot_eval.log 2>&1
done
echo FINI >> resultats-bruts/lot_eval.log
