# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
from __future__ import annotations
import numpy as np


def lhs(n_samples: int, n_dim: int, seed: int = 42) -> np.ndarray:
    """
    Latin Hypercube Sampling in [0,1], shape (n_samples, n_dim).
    """
    rng = np.random.default_rng(seed)
    cut = np.linspace(0.0, 1.0, n_samples + 1)
    u = rng.random((n_samples, n_dim))
    a = cut[:-1]
    b = cut[1:]
    H = u * (b - a)[:, None] + a[:, None]
    for j in range(n_dim):
        rng.shuffle(H[:, j])
    return H

