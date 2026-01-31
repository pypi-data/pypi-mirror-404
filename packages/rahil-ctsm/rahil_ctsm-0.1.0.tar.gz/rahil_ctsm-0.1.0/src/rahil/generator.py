from __future__ import annotations

import os
from os import path
import numpy as np
import pandas as pd
import xarray as xr

from .lhs_sampler import lhs
from .data_manager import ensure_defaults

DEFAULT_PFTS = {
    "corn": 17,
    "soybean": 23,
    "wheat": 19,
}

DEFAULT_BOUNDS_COLS = {
    "corn":    ("corn min", "corn max"),
    "soybean": ("soybean min", "soybean max"),
    "wheat":   ("wheat min", "wheat max"),
}


def _find_pft_dim(da: xr.DataArray) -> str:
    for d in da.dims:
        if "pft" in d.lower():
            return d
    raise ValueError(f"Can't find a PFT dimension in dims={da.dims}")


def _cast_like_base(param: str, base_dtype, new_val_float: float):
    if param == "mxmat":
        v = float(new_val_float)
        if abs(v) > 1.0e6:
            v = v / (86400.0 * 1.0e9)  # ns -> days
        return int(np.rint(v))

    if np.issubdtype(base_dtype, np.integer):
        return int(np.rint(new_val_float))

    return float(new_val_float)


def _read_bounds(bounds_path: str) -> pd.DataFrame:
    ext = os.path.splitext(bounds_path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(bounds_path)
    else:
        df = pd.read_csv(bounds_path, sep=",", engine="python", encoding="utf-8-sig")

    df = df.dropna(axis=1, how="all")
    df.columns = df.columns.astype(str).str.strip()

    # normalize parameter column name -> "Parameters"
    rename_map = {}
    if "parameter" in df.columns: rename_map["parameter"] = "Parameters"
    if "Parameter" in df.columns: rename_map["Parameter"] = "Parameters"
    if "PARAMETER" in df.columns: rename_map["PARAMETER"] = "Parameters"
    df = df.rename(columns=rename_map)
    return df


def generate_lhs(
    location: str = "pe_crops",
    iteration: int = 0,
    Ninit: int = 150,
    seed: int = 42,
    out_param_dir: str | None = None,
    out_workflow_dir: str = "workflow",
    basepftfile: str | None = None,
    csv_file: str | None = None,   # can be xlsx
    pfts: dict | None = None,
    bounds_cols: dict | None = None,
) -> dict:
    """
    Generate LHS ensembles and NetCDF param files for corn/soy/wheat.

    If basepftfile/csv_file are None, uses packaged defaults
    copied into ~/.rahil/data.
    """
    if basepftfile is None or csv_file is None:
        d_base, d_bounds = ensure_defaults()
        basepftfile = d_base if basepftfile is None else basepftfile
        csv_file = d_bounds if csv_file is None else csv_file

    pfts = DEFAULT_PFTS if pfts is None else pfts
    bounds_cols = DEFAULT_BOUNDS_COLS if bounds_cols is None else bounds_cols

    if out_param_dir is None:
        out_param_dir = f"./paramfile/{location}/"

    os.makedirs(out_param_dir, exist_ok=True)
    os.makedirs(out_workflow_dir, exist_ok=True)

    # 1) Read bounds
    pf = _read_bounds(csv_file)

    need_cols = ["Parameters"]
    for crop in ["corn", "soybean", "wheat"]:
        need_cols.extend(list(bounds_cols[crop]))

    missing_cols = [c for c in need_cols if c not in pf.columns]
    if missing_cols:
        raise KeyError(
            f"Missing columns in bounds table: {missing_cols}\n"
            f"Available: {list(pf.columns)}\n"
            f"Bounds file used: {csv_file}"
        )

    pf = pf[need_cols].copy()
    pf = pf.dropna(subset=["Parameters"])
    pf["Parameters"] = pf["Parameters"].astype(str).str.strip()
    param_list = pf["Parameters"].values

    # 2) Build xlb/xub + var_map
    xlb, xub, var_map = [], [], []
    for _, row in pf.iterrows():
        param = row["Parameters"]

        mn, mx = bounds_cols["corn"]
        xlb.append(float(row[mn])); xub.append(float(row[mx]))
        var_map.append((param, "corn", int(pfts["corn"])))

        mn, mx = bounds_cols["soybean"]
        xlb.append(float(row[mn])); xub.append(float(row[mx]))
        var_map.append((param, "soybean", int(pfts["soybean"])))

        mn, mx = bounds_cols["wheat"]
        xlb.append(float(row[mn])); xub.append(float(row[mx]))
        var_map.append((param, "wheat", int(pfts["wheat"])))

    xlb = np.array(xlb, dtype=float)
    xub = np.array(xub, dtype=float)
    nInput = len(xlb)

    # 3) LHS scale
    X01 = lhs(Ninit, nInput, seed=seed)
    perturbed_param = X01 * (xub - xlb) + xlb

    # 4) Case IDs + workflow
    test_id_list = [f"{location}_{iteration}_{i:04d}" for i in range(Ninit)]
    colnames = [f"{p}__pft{pid}_{tag}" for (p, tag, pid) in var_map]
    psets_df = pd.DataFrame(perturbed_param, columns=colnames, index=test_id_list)

    # mxmat conversion in TXT
    for c in psets_df.columns:
        if c.startswith("mxmat__"):
            v = psets_df[c].astype(float).to_numpy()
            v = np.where(np.abs(v) > 1.0e6, v / (86400.0 * 1.0e9), v)
            psets_df[c] = np.rint(v).astype(int)

    param_list_txt = path.join(out_workflow_dir, f"{location}_{iteration}.param_list.txt")
    psets_df.to_csv(param_list_txt)

    main_run = path.join(out_workflow_dir, f"{location}_{iteration}.main_run.txt")
    with open(main_run, "w") as f:
        f.write("\n".join(psets_df.index.values) + "\n")

    # 5) Write NetCDF files
    base = xr.open_dataset(basepftfile, decode_times=False)
    missing_params = [p for p in param_list if p not in base.variables]
    if missing_params:
        base.close()
        raise KeyError(f"These parameters are not in the NetCDF: {missing_params}")

    param_meta = {}
    for p in param_list:
        da = base[p]
        pft_dim = _find_pft_dim(da)
        other_dims = [d for d in da.dims if d != pft_dim]
        param_meta[p] = {"pft_dim": pft_dim, "dtype": da.dtype, "other_dims": other_dims}
    base.close()

    for case_id, row in psets_df.iterrows():
        tmp = xr.open_dataset(basepftfile, decode_times=False)
        encoding = {}

        for (param, tag, pid) in var_map:
            col = f"{param}__pft{pid}_{tag}"
            new_val = float(row[col])

            meta = param_meta[param]
            pft_dim = meta["pft_dim"]
            base_dtype = meta["dtype"]
            other_dims = meta["other_dims"]

            casted = _cast_like_base(param, base_dtype, new_val)

            if len(other_dims) == 0:
                tmp[param].loc[{pft_dim: pid}] = casted
            else:
                indexer = {pft_dim: pid}
                for d in other_dims:
                    indexer[d] = slice(None)
                tmp[param].loc[indexer] = casted

            if param == "mxmat":
                mx = tmp["mxmat"]
                mxv = np.array(mx, dtype="float64")
                mask_ns = np.isfinite(mxv) & (np.abs(mxv) > 1.0e6)
                mxv[mask_ns] = mxv[mask_ns] / (86400.0 * 1.0e9)
                mxv = np.rint(mxv)
                mxv = np.where(np.isfinite(mxv), mxv, 0.0)

                tmp["mxmat"] = xr.DataArray(mxv.astype("int32"), dims=mx.dims, coords=mx.coords)
                tmp["mxmat"].attrs["units"] = "days"
                tmp["mxmat"].attrs["coordinates"] = "pftname"
                tmp["mxmat"].attrs.pop("_FillValue", None)
                encoding["mxmat"] = {"dtype": "i4", "_FillValue": 0}

        out_nc = path.join(out_param_dir, f"{case_id}.nc")
        tmp.to_netcdf(out_nc, mode="w", encoding=encoding)
        tmp.close()

    return {
        "param_dir": out_param_dir,
        "workflow_dir": out_workflow_dir,
        "param_list_txt": param_list_txt,
        "main_run": main_run,
        "psets_df": psets_df,
        "basepftfile_used": basepftfile,
        "bounds_used": csv_file,
    }
