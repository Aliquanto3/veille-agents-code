#!/usr/bin/env bash
# T4 : lance la mutation bornee sur les 5 stories, une a la fois (un seul outil de mutation a la fois).
# Prerequis : copies jetables creees avec `git worktree add --detach` (voir resultats-mutation.md).
S="${S:?dossier des copies jetables}"; T="$(dirname "$0")"; PY="${PY:-python}"
UI="src/usine/ui"
cd "$T"
$PY mutation_story.py --story wd-8-4 --worktree "$S/wd-8-4" --base '462f726^' \
  --modules src/wavedevsecops/ci/findings.py,src/wavedevsecops/scenarios/ops/replace_in_file.py,src/wavedevsecops/toolrun/__init__.py,src/wavedevsecops/ci/__init__.py \
  --tests tests/test_quality_gate.py --timeout-test 180 --out resultats-bruts
$PY mutation_story.py --story us-7-14 --worktree "$S/us-7-14" --base '9e4639c^' --sync \
  --modules $UI/carte.py,$UI/detail.py,$UI/vues.py,$UI/serveur.py,$UI/cli.py,$UI/liens.py \
  --tests tests/unit/ui/test_vues_ecrans.py,tests/unit/ui/test_serveur.py,tests/contrat/consultation/test_contrat.py --out resultats-bruts
$PY mutation_story.py --story us-7-15 --worktree "$S/us-7-15" --base 'd58ce6c^' --sync \
  --modules $UI/chaine.py,$UI/vues.py,$UI/serveur.py,$UI/app.py,$UI/textes.py \
  --tests tests/unit/ui/test_chaine.py,tests/unit/ui/test_serveur.py,tests/unit/ui/test_vues_ecrans.py,tests/unit/ui/test_cli.py --out resultats-bruts
$PY mutation_story.py --story us-7-16 --worktree "$S/us-7-16" --base '5545523^' --sync \
  --modules $UI/ecrans.py,$UI/outillage.py,$UI/pseudonymisation.py,$UI/vues.py,$UI/serveur.py,$UI/cli.py \
  --tests tests/unit/ui/test_ecrans_web.py,tests/unit/ui/test_vues_ecrans.py,tests/unit/ui/test_serveur.py,tests/unit/ui/test_chaine.py --out resultats-bruts
