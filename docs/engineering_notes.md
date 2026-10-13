# Engineering Notes

## Coupling convention

The CFD patch normals are treated as **outward normals of the fluid domain**. On an immersed solid wall they therefore point into the solid. The pressure force exerted by the fluid on the structure is

\[
\mathbf F_i = p_i A_i \mathbf n_{f,i}.
\]

For the chosen panel, flow is +x. The upstream/front wall has fluid-domain normal +x and the downstream/back wall has fluid-domain normal -x, so the net structural pressure is

\[
\Delta p = p_{front} - p_{back}.
\]

The mapper projects both surface pressure distributions onto the x=0 shell midsurface and interpolates in local (y,z) coordinates.

## Why one-way FSI

The data path is OpenFOAM pressure -> Python transfer -> CalculiX static response. Structural displacement is not sent back to OpenFOAM. This is valid only when deformation causes negligible change to the flow/load state. The appropriate posterior check is a deformed-geometry CFD sensitivity run, not an unsupported assertion that displacement is "small".

## Mapping

Two methods are implemented:

- nearest neighbour: robust baseline and useful sensitivity bound;
- piecewise-linear interpolation on a Delaunay triangulation, with nearest fallback only outside the convex hull.

Interpolation is not inherently conservative. The project therefore reports force and root-moment errors instead of silently rescaling the field.

## Conservation checks

The transfer is validated against both resultant force and root moment. Matching force alone can hide a badly misplaced pressure distribution.

## Structural model

The production deck uses CalculiX S4 shells on the midsurface. A separate Euler-Bernoulli beam FE model is included only as an independently executable reference/sanity check. It must not be presented as the CalculiX result.

## CFD assumptions

The supplied OpenFOAM Foundation v13 case is steady incompressible RANS with k-omega SST around a thin bluff plate. This is a pressure-transfer demonstrator, not a high-fidelity aerodynamic benchmark. A separated plate wake can be unsteady; if residuals and forces fail to reach a steady mean, the correct upgrade is transient incompressibleFluid/PIMPLE with time-averaged wall pressure.

Boundary-layer resolution must be inspected through y+ after the real run. The snappyHexMesh case includes three prism layers, but layer quality/y+ are machine-run verification items, not pre-claimed results.

## OpenFOAM pressure units

Foundation OpenFOAM incompressible `p` has dimensions [0 2 -2 0 0 0 0], i.e. kinematic pressure m^2/s^2. The extractor converts it to Pa as `p_pa = rho * p`.

## Main error sources

1. CFD discretisation and turbulence modelling.
2. Finite domain/blockage effects.
3. Wall treatment and near-wall mesh quality.
4. Pressure extraction at boundary owner cells.
5. Surface-to-shell interpolation.
6. Neglect of viscous shear in the structural load transfer.
7. Structural shell discretisation.
8. One-way coupling assumption.
9. Static-response assumption (no flutter/vortex-induced dynamic response).
