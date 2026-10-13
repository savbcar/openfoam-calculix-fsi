# Interview Defence

**What is FSI?**  Coupling between fluid tractions and structural response. In two-way FSI the deformed/moving structure also changes the fluid domain and loads.

**Why one-way here?**  OpenFOAM is solved on the undeformed geometry, its pressure is mapped once to CalculiX, and the structure is solved statically. No structural displacement is returned to CFD.

**When is it invalid?**  When deformation materially changes incidence, blockage, separation, or unsteady fluid loading; or when aeroelastic instability/dynamic coupling matters.

**How is pressure mapped?**  Front and back immersed-wall faces are classified from the fluid-domain normals, projected to the shell midsurface, and interpolated in panel-local (y,z) coordinates. Linear Delaunay interpolation is primary; nearest-neighbour is a sensitivity baseline.

**Is the transfer conservative?**  It is measured, not assumed. Integrated CFD pressure force and root moment are compared with the mapped shell load. Raw interpolation errors are reported.

**How are coordinates verified?**  The project uses an explicit global convention: flow +x, cantilever y=0..L, span z=-b/2..b/2, shell midsurface x=0. Tests verify geometry area and normal conventions.

**Why check moment as well as force?**  Two load distributions can have the same total force but different centres of pressure and therefore different cantilever bending response.

**How is deformation validated?**  A beam FE reference is checked exactly against the Euler-Bernoulli uniform-load solution. The real shell solution is then compared for order-of-magnitude consistency and mesh convergence.

**What does two-way FSI require?**  Repeated field transfer in both directions, mesh motion/remeshing, convergence of interface displacement/traction, relaxation/acceleration, and time synchronisation for transient coupling.
