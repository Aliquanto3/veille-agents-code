#!/bin/sh
# usage : lot_claude.sh id1,id2,... ; haiku puis opus, 2 sessions au plus
cd "$(dirname "$0")"
uv run --no-project --python 3.14 python revue_claude.py haiku --stories "$1" --jobs 2
uv run --no-project --python 3.14 python revue_claude.py opus --stories "$1" --jobs 2
