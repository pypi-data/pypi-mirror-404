# rahil

Generate CLM/CTSM PFT parameter NetCDF ensembles using Latin Hypercube Sampling.

## Usage

```python
import rahil
out = rahil.generate_lhs(location="pe_crops", iteration=0, Ninit=10, seed=1)
print(out["param_dir"])
