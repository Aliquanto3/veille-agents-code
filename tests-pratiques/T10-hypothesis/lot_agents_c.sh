#!/usr/bin/env bash
# T10b : lance les agents du bras C, deux voies en parallele (2 sessions claude -p au plus), chaque voie en sequence.
# usage : lot_agents_c.sh "<story>:<essai> ..." "<story>:<essai> ..."   (variables T10_RACINE et T10_BRUTS requises)
cd "$(dirname "$0")"; export MSYS_NO_PATHCONV=1 PYTHONUTF8=1
voie() { for it in $1; do s="${it%%:*}"; e="${it##*:}"
  [ -s "$T10_BRUTS/agent-$s-C$e.json" ] && continue
  uv run python lancer_agent.py "$s" C "$e" > "$T10_BRUTS/log-$s-C$e.txt" 2>&1; done; }
voie "$1" & voie "$2" & wait
echo FINI
