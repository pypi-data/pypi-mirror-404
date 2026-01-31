from __future__ import annotations

import os
from os import path
import shutil
import urllib.request

try:
    from importlib.resources import files as ir_files
except Exception:
    ir_files = None


# ============================================================
# >>>> EDIT ONLY THESE THREE LINES <<<<
# ============================================================
GITHUB_USER = "M-Uzair-Rahil"
GITHUB_REPO = "CLM"
RELEASE_TAG = "v0.1.0"
# ============================================================

BASE_NC_NAME = "clm50_params.c240207b.nc"
BOUNDS_XLSX_NAME = "finalized_params_for_run.xlsx"

BASE_NC_URL = (
    f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/download/"
    f"{RELEASE_TAG}/{BASE_NC_NAME}"
)


def _user_data_dir() -> str:
    return path.expanduser("~/.rahil/data")


def _download(url: str, dst: str) -> None:
    """Download file atomically (safe for interruptions)."""
    os.makedirs(path.dirname(dst), exist_ok=True)
    tmp = dst + ".part"
    with urllib.request.urlopen(url) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    os.replace(tmp, dst)


def ensure_defaults() -> tuple[str, str]:
    """
    Ensure default base NetCDF + bounds Excel exist in ~/.rahil/data.

    - bounds Excel is bundled inside the PyPI wheel
    - base NetCDF is downloaded from GitHub Releases on first use

    Returns:
        (base_nc_path, bounds_xlsx_path)
    """
    data_dir = _user_data_dir()
    os.makedirs(data_dir, exist_ok=True)

    out_base = path.join(data_dir, BASE_NC_NAME)
    out_bounds = path.join(data_dir, BOUNDS_XLSX_NAME)

    # --------------------------------------------------------
    # 1) Bounds Excel: copy from package into ~/.rahil/data
    # --------------------------------------------------------
    if not path.exists(out_bounds):
        if ir_files is None:
            raise RuntimeError("importlib.resources.files not available.")

        pkg_bounds = ir_files("rahil").joinpath("data").joinpath(BOUNDS_XLSX_NAME)
        if not pkg_bounds.exists():
            raise FileNotFoundError(f"Missing packaged bounds file: {pkg_bounds}")

        shutil.copyfile(str(pkg_bounds), out_bounds)

    # --------------------------------------------------------
    # 2) Base NetCDF: download from GitHub Release if missing
    # --------------------------------------------------------
    if not path.exists(out_base):
        if "YOUR_GITHUB_USERNAME" in BASE_NC_URL:
            raise RuntimeError(
                "GitHub release URL not configured.\n"
                "Edit GITHUB_USER / GITHUB_REPO / RELEASE_TAG in data_manager.py"
            )
        _download(BASE_NC_URL, out_base)

    return out_base, out_bounds
