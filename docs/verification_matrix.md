# Verification Matrix

| Item | Method | Automated here? | Real-solver gate |
|---|---|---:|---:|
| Shell geometry area/normal | unit test | yes | no |
| Uniform-load beam FE | exact Euler-Bernoulli solution | yes | no |
| Linear pressure interpolation | synthetic known field | yes | no |
| Force transfer | CFD-surface vs mapped sum | yes | repeat with real CFD |
| Root-moment transfer | CFD-surface vs mapped sum | yes | repeat with real CFD |
| OpenFOAM ASCII parser | fixture tests | yes | real case after solve |
| CalculiX deck writer | keyword/load-count tests | yes | run `ccx` |
| CalculiX DAT displacement parser | fixture test | yes | run `ccx` |
| CalculiX DAT stress parser | fixture test | yes | run `ccx` |
| CFD mesh sensitivity | 3-level campaign script | no (OpenFOAM unavailable here) | yes |
| FEA shell mesh sensitivity | 3-level campaign script | no (CalculiX unavailable here) | yes |
| One-way assumption | deformed-geometry rerun | no | yes |
