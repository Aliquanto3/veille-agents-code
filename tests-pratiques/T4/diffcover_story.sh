#!/usr/bin/env bash
# Bonus T4 : couverture differentielle (diff-cover) d'une story, memes tests que la mutation.
# usage : diffcover_story.sh <copie jetable> <base> <src a mesurer> <tests...>
wt="$1"; base="$2"; srcdir="$3"; shift 3
cd "$wt" || exit 2
V=.venv/Scripts
uv pip install -q diff-cover pytest-cov >/dev/null 2>&1
rm -f .coverage coverage.xml
start=$(date +%s)
$V/python.exe -m pytest -q --tb=no -p no:cacheprovider --cov="$srcdir" --cov-report=xml:coverage.xml "$@" 2>&1 | tail -1
$V/diff-cover coverage.xml --compare-branch="$base" --fail-under=80 --format json:diff-cover.json 2>&1 | tail -12
echo "diff-cover rc=${PIPESTATUS[0]} duree=$(( $(date +%s) - start ))s"
