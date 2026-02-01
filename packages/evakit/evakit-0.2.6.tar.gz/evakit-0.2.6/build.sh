#!/usr/bin/env bash
set -Eeuxo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}" && pwd -P)"

cd "${PROJECT_ROOT}"

python -m build
python -m twine check dist/*
python -m twine upload dist/*
