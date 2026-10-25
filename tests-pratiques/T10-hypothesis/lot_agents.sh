#!/usr/bin/env bash
# T10 : lance les agents par paires (A et B en parallele, 2 sessions claude -p au plus), une story et un essai a la fois.
# usage : lot_agents.sh "<story>:<essai> <story>:<essai> ..."
cd "$(dirname "$0")"; export MSYS_NO_PATHCONV=1 PYTHONUTF8=1
for it in $1; do
  s="${it%%:*}"; e="${it##*:}"
  [ -s "resultats-bruts/agent-$s-A$e.json" ] && continue
  uv run python lancer_agent.py "$s" A "$e" > "resultats-bruts/log-$s-A$e.txt" 2>&1 &
  uv run python lancer_agent.py "$s" B "$e" > "resultats-bruts/log-$s-B$e.txt" 2>&1 &
  wait
done
echo FINI
