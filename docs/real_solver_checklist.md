# Real-solver verification checklist

Do not claim a numerical result from OpenFOAM or CalculiX until this checklist is completed on a machine with those solvers.

- `foamVersion` reports OpenFOAM-13 and `foamRun -help` works.
- `blockMesh`, `snappyHexMesh -overwrite`, `checkMesh`, and `foamRun` all complete.
- Inspect `checkMesh` for non-orthogonality, skewness and illegal faces.
- Inspect prism-layer coverage on `panel` and calculate/plot y+.
- Verify steady force history; if it oscillates persistently, use transient averaging.
- Confirm `p` is written ASCII and has dimensions `[0 2 -2 0 0 0 0]`.
- Compare Python-integrated pressure force against an OpenFOAM force/function-object calculation.
- Run coarse/medium/fine CFD meshes and compare Fx, root Mz and mapped tip displacement.
- Run CalculiX uniform-pressure benchmark before mapped load.
- Confirm shell pressure sign by checking that positive net front pressure produces +x panel displacement.
- Run coarse/medium/fine shell meshes and compare tip displacement and stress sensitivity; treat peak stress at the exact clamped edge cautiously because it may remain mesh/singularity sensitive.
- Record exact solver versions and commit only generated plots/tables that were actually run.
