#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
: "${FOAM_INST_DIR:=/opt/openfoam13}"
if [[ -f "$FOAM_INST_DIR/etc/bashrc" ]]; then source "$FOAM_INST_DIR/etc/bashrc"; fi
python -m fsi.cli --help >/dev/null
(
  cd cases/openfoam13/panel
  ./Allrun
)
mkdir -p results/real
python -m fsi.cli extract-openfoam --case cases/openfoam13/panel --patch panel --time latest --density 1.20 --out results/real/cfd_surface.csv
python -m fsi.cli couple --config config/baseline.yaml --surface results/real/cfd_surface.csv --out results/real/calculix
if command -v ccx >/dev/null; then
  (cd results/real/calculix && ccx -i panel | tee log.ccx)
else
  echo "ccx not found: CalculiX deck generated but structural solve skipped." >&2
fi
