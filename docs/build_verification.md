# Build Verification Snapshot

Build date: 2026-10-12.

This file records what was actually executed when the portfolio repository was assembled. It deliberately separates verified Python/coupling behavior from solver paths that require the user's WSL installation.

## Executed successfully in the build environment

- Python source compilation for `src/`, `tests/`, and `scripts/`.
- Shell syntax checks for `Allrun`, `Allclean`, `run_real_pipeline.sh`, and `run_synthetic.sh`.
- `pytest -q`: **10 passed**.
- Deterministic end-to-end synthetic pipeline through the installed CLI entry point.
- Editable package install from `pyproject.toml` with local dependencies already present.
- CLI argument parsing for the main program and both convergence-study drivers.
- Generation of CFD-surface CSV, mapped-pressure CSV, CalculiX S4 input deck, JSON/Markdown report, and four PNG verification figures.
- Visual inspection of the generated mapped-pressure plot.

Reference synthetic transfer result:

| Metric | Value |
|---|---:|
| reference surface force Fx | 6.785626942 N |
| mapped structural force Fx | 6.785218824 N |
| force-transfer error | 0.006014% |
| reference root moment Mz | -1.006745400 N m |
| mapped root moment Mz | -1.006698767 N m |
| root-moment transfer error | 0.004632% |
| beam-reference tip deflection | 4.0661 mm |
| beam-reference root bending stress | 12.5837 MPa |

These values come from the deterministic **synthetic verification field**, not an OpenFOAM or CalculiX solution. They are valid evidence for the mapper/conservation/reference implementation only.

## Not executable in the build environment

- OpenFOAM Foundation 13: `foamVersion` / `foamRun` binaries are not installed here.
- CalculiX: `ccx` is not installed here.
- Docker: the Docker CLI/daemon is not available here.
- Ruff: the Ruff executable is not installed here; Ruff is declared in the dev dependencies and executed by GitHub Actions.

Therefore no OpenFOAM force, CalculiX displacement/stress, real CFD/FEA mesh-convergence number, y+, or deformed-geometry one-way-validity result is claimed in this repository snapshot.

## Required real-solver completion gates

Run `docs/real_solver_checklist.md` on the target WSL machine before putting real CFD/FEA numbers on a CV. The supplied scripts are designed to make those checks reproducible rather than manual.
