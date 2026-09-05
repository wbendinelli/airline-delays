"""`reports/summary.json`: every headline number the READMEs quote, read from the artefacts.

Nothing here is computed from raw data and nothing is typed: each value is read
from a committed manifest, report or table, so a number in the prose can always
be traced to the file that printed it. The file carries no timestamp; `meta`
records the inputs and the commit, and the freshness test compares everything
but `meta`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import median
from typing import Any

from airline_delays import paths
from airline_delays.definitions import nodes as nodes_mod
from airline_delays.estimation.specification import REQUIRED_COLUMNS
from airline_delays.staging import git_commit

SUMMARY_PATH: Path = paths.REPORTS / "summary.json"


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parquet_shape(path: Path) -> tuple[int, int]:
    import pyarrow.parquet as pq

    metadata = pq.read_metadata(path)
    return metadata.num_rows, metadata.num_columns


def _reconstruction(previous: dict[str, Any]) -> dict[str, Any]:
    import pandas as pd

    raw = _json(paths.RAW / "manifest.json")
    years = sorted({int(entry["year"]) for entry in raw["files"]})
    retrieved = sorted(entry["retrieved_at"] for entry in raw["files"])
    fetch_minutes = None
    if retrieved:
        from datetime import datetime

        first, last = (datetime.fromisoformat(retrieved[0]), datetime.fromisoformat(retrieved[-1]))
        fetch_minutes = round((last - first).total_seconds() / 60, 1)
    out: dict[str, Any] = {
        "raw": {
            "files": raw["n_files"],
            "bytes": raw["total_bytes"],
            "gigabytes": round(raw["total_bytes"] / 1e9, 2),
            "years": [years[0], years[-1]],
            "retrieved_on": raw["generated_at"][:10],
            "fetch_minutes": fetch_minutes,
        }
    }
    staged_manifest = paths.STAGED / "manifest.json"
    if staged_manifest.exists():
        staged = _json(staged_manifest)
        out["staged"] = {
            "rows": staged["total_rows"],
            "years": len(staged["years"]),
            "partitions": len(staged["years"]),
        }
    else:
        # The staged layer is regenerated, not committed: without its manifest the
        # committed block is carried forward unchanged (meta.inputs says so).
        out["staged"] = dict(previous.get("reconstruction", {}).get("staged", {}))
    fact_manifest = _json(paths.ANALYSIS / "manifest.json")
    fact_rows, fact_columns = _parquet_shape(paths.ANALYSIS / "fact_group_route_month.parquet")
    out["fact"] = {
        "rows": fact_rows,
        "columns": fact_columns,
        "route_months": fact_manifest["route_months"],
        "node_day_hours": fact_manifest["node_day_hours"],
        "outlier_threshold_min": fact_manifest["outlier_threshold_min"],
        "seconds": fact_manifest["seconds"],
    }
    panel_manifest = _json(paths.ANALYSIS / "panel_manifest.json")
    panel = pd.read_parquet(paths.ANALYSIS / "panel_route_month.parquet", columns=["route", "ym"])
    _, panel_columns = _parquet_shape(paths.ANALYSIS / "panel_route_month.parquet")
    out["panel"] = {
        "rows": len(panel),
        "columns": panel_columns,
        "routes": int(panel["route"].nunique()),
        "months": int(panel["ym"].nunique()),
        "ym_range": [int(panel["ym"].min()), int(panel["ym"].max())],
        "nodes": len(nodes_mod.PANEL_NODES),
        "parquet_bytes": panel_manifest["parquet_bytes"],
        "csv_bytes": panel_manifest["csv_bytes"],
        "seconds": panel_manifest["seconds"],
    }
    for name in ("city_month", "airline_city_month"):
        rows, columns = _parquet_shape(paths.ANALYSIS / f"{name}.parquet")
        out[name] = {"rows": rows, "columns": columns}
    fact = pd.read_parquet(
        paths.ANALYSIS / "fact_group_route_month.parquet", columns=["ym", "flights", "realized"]
    )
    by_year = fact.assign(year=fact["ym"] // 100).groupby("year")[["flights", "realized"]].sum()
    out["flights_by_year"] = {
        str(int(year)): {"scheduled": int(row["flights"]), "realised": int(row["realized"])}
        for year, row in by_year.iterrows()
    }
    first, last = int(by_year.index.min()), int(by_year.index.max())
    out["flights_scheduled_first_year"] = int(by_year.loc[first, "flights"])
    out["flights_scheduled_last_year"] = int(by_year.loc[last, "flights"])
    out["flights_growth_pct"] = round(
        100 * (by_year.loc[last, "flights"] / by_year.loc[first, "flights"] - 1), 1
    )
    columns_in_panel = set(_parquet_columns(paths.ANALYSIS / "panel_route_month.parquet"))
    aliases = {"od": "route"}
    missing = []
    for name in REQUIRED_COLUMNS:
        actual = aliases.get(name, name)
        if actual not in columns_in_panel:
            if name not in ("o_region", "d_region"):
                missing.append(name)
            continue
    all_null = [
        name
        for name in ("rthhi", "maxcthhi")
        if name in columns_in_panel
        and pd.read_parquet(paths.ANALYSIS / "panel_route_month.parquet", columns=[name])[name]
        .isna()
        .all()
    ]
    out["article_columns_missing"] = sorted(set(missing) | set(all_null))
    return out


def _parquet_columns(path: Path) -> list[str]:
    import pyarrow.parquet as pq

    return list(pq.read_schema(path).names)


def _article_panel() -> dict[str, Any]:
    manifest = _json(paths.ANALYSIS / "article_panel_manifest.json")
    files = manifest["files"]
    return {
        "rows": manifest["rows"],
        "columns": manifest["columns"],
        "routes": manifest["routes"],
        "months": manifest["months"],
        "ym_range": manifest["ym_range"],
        "source_header_timestamp": manifest["source"].get("stata_header_timestamp"),
        "variables_in_source": manifest["source"].get("variables_in_source"),
        "rows_in_source": manifest["source"].get("rows_in_source"),
        "parquet_bytes": files["article_panel_route_month.parquet"]["bytes"],
        "csv_bytes": files["article_panel_route_month.csv.gz"]["bytes"],
    }


def _published() -> dict[str, Any]:
    from airline_delays.estimation.published import load

    published = load()
    out: dict[str, Any] = {}
    for table in ("table3", "table6"):
        columns = published[table]["columns"]
        cells = {}
        for key in ("1", "2"):
            column = columns[key]
            cells[f"col{key}"] = {
                "regressand": column["regressand"],
                "n_obs": column["stats"].get("n_obs"),
                **{
                    name: {
                        "b": column["b"].get(name),
                        "se": column["se"].get(name),
                        "stars": column.get("stars", {}).get(name, ""),
                    }
                    for name in ("rthhi", "maxcthhi", "lcc", "maxalccfu")
                    if name in column["b"]
                },
            }
        out[table] = cells
    return out


def _estimation() -> dict[str, Any]:
    summary = _json(paths.REPLICATION_REPORTS / "summary.json")
    results = _json(paths.REPLICATION_REPORTS / "results.json")
    tables = {}
    published_n, replicated_n = [], []
    for name in ("table3", "table4", "table5", "table6", "table7"):
        block = summary[name]
        tables[name] = {
            key: block[key]
            for key in (
                "n_coefficients",
                "sign_agreement",
                "within_half_se",
                "median_difference_in_se",
                "max_difference_in_se",
                "median_se_ratio",
            )
        }
        for cell in block["n_obs"].values():
            if cell["published"] is not None:
                published_n.append(cell["published"])
            if cell["replicated"] is not None:
                replicated_n.append(cell["replicated"])
    totals = {
        "coefficients": sum(t["n_coefficients"] for t in tables.values()),
        "sign_agreement": sum(t["sign_agreement"] for t in tables.values()),
        "within_half_se": sum(t["within_half_se"] for t in tables.values()),
        "max_difference_in_se": max(t["max_difference_in_se"] for t in tables.values()),
    }
    totals["within_half_se_pct"] = round(100 * totals["within_half_se"] / totals["coefficients"], 1)
    hhi = summary["hhi_sign_inversions"]
    table2 = results["table2"]
    meta = results["meta"]
    return {
        "tables": tables,
        "totals": totals,
        "hhi": {
            key: hhi[key]
            for key in (
                "n_comparisons",
                "n_inverted_published",
                "n_inverted_replicated",
                "n_inversion_replicates",
                "n_pattern_agrees",
                "columns_with_inversion",
            )
        },
        "sample": {
            key: meta["sample"][key]
            for key in (
                "n_raw",
                "routes_raw",
                "n_after_missing_regressand",
                "n_after_singleton_cut",
                "routes",
                "months",
            )
        },
        "n_obs_published_range": [min(published_n), max(published_n)],
        "n_obs_replicated_range": [min(replicated_n), max(replicated_n)],
        "n_obs_excess_pct": round(100 * (sum(replicated_n) / sum(published_n) - 1), 1),
        "table2": {
            "n_variables": len(table2["replicated"]["variables"]),
            "n_correlations": table2["comparison"]["n_correlations"],
            "median_abs_correlation_difference": table2["comparison"][
                "median_abs_correlation_difference"
            ],
            "max_abs_correlation_difference": table2["comparison"][
                "max_abs_correlation_difference"
            ],
        },
        "bandwidth": meta["bandwidth"],
        "seconds": meta["seconds"],
    }


def _prediction() -> dict[str, Any]:
    dataset = _json(paths.PREDICTION_REPORTS / "dataset.json")
    rolling = _json(paths.PREDICTION_REPORTS / "rolling.json")
    fixed = _json(paths.PREDICTION_REPORTS / "fixed.json")
    leakage_path = paths.PREDICTION_REPORTS / "leakage.json"
    leakage = _json(leakage_path) if leakage_path.exists() else {}
    checks = leakage.get("checks", leakage) if isinstance(leakage, dict) else leakage
    horizons: dict[str, Any] = {}
    for horizon in rolling["meta"]["horizons"]:
        aucs = [fold["models"][horizon]["auc"] for fold in rolling["folds"]]
        entry = {"auc_min": min(aucs), "auc_median": median(aucs), "auc_max": max(aucs)}
        for metric in ("pr_auc", "brier"):
            values = [fold["models"][horizon].get(metric) for fold in rolling["folds"]]
            if all(v is not None for v in values):
                entry[f"{metric}_median"] = median(values)
        linked = [fold["linked_subset"][horizon]["auc"] for fold in rolling["folds"]]
        entry["linked_subset_auc_min"] = min(linked)
        entry["linked_subset_auc_max"] = max(linked)
        horizons[horizon] = entry
    baselines = {}
    for name in rolling["folds"][0]["baselines"]:
        aucs = [fold["baselines"][name]["auc"] for fold in rolling["folds"]]
        baselines[name] = {"auc_min": min(aucs), "auc_max": max(aucs)}
    linked_share = [fold["linked_share_test"] for fold in rolling["folds"]]
    fixed_folds = {
        fold["target"]: {h: fold["models"][h]["auc"] for h in fold["models"]}
        for fold in fixed["folds"]
    }
    window = dataset["accounting"]["legacy_window"]
    return {
        "rows": dataset["rows"],
        "years": [min(dataset["years"]), max(dataset["years"])],
        "features_d1": len(dataset["features_d1"]),
        "features_h1_only": len(dataset["features_h1_only"]),
        "targets": len(dataset["targets"]),
        "leakage_checks": len(checks) if hasattr(checks, "__len__") else None,
        "rolling": {
            "target": rolling["target"],
            "test_years": [fold["test_years"][0] for fold in rolling["folds"]],
            "folds": len(rolling["folds"]),
            "horizons": horizons,
            "baselines": baselines,
            "linked_share_min": min(linked_share),
            "linked_share_max": max(linked_share),
            "learner": rolling["meta"]["learner"],
        },
        "fixed": fixed_folds,
        "legacy_window": {
            key: window[key]
            for key in (
                "years",
                "realised_in_scope",
                "realised_out_of_scope",
                "null_arrival_rate_in_scope",
                "null_arrival_rate_out_of_scope",
                "targets_available",
            )
        },
        "runtime_seconds": dataset["runtime"]["total_seconds"],
        "dataset_build_seconds": dataset["runtime"]["dataset_build_seconds"],
    }


def _theory() -> dict[str, Any]:
    model = _json(paths.THEORY_REPORTS / "model.json")
    figures = _json(paths.THEORY_REPORTS / "figures.json")
    return {
        "n_identities": model["meta"]["n_identities"],
        "n_holding": sum(1 for identity in model["identities"] if identity.get("holds")),
        "n_figures": len(figures["figures"]),
        "leader_toll_share_linear": model["tolls"]["leader_over_MCD_linear"],
        "cournot_toll_share": model["tolls"]["cournot_over_MCD"],
        "atomistic_toll_share": model["tolls"]["atomistic_over_MCD"],
        "leader_follower": model["leader_follower"]["statement"],
    }


def _registry() -> dict[str, Any]:
    from airline_delays.schema import built_layers

    layers = built_layers(paths.REPO_ROOT)
    return {
        "layers": len(layers),
        "columns_total": sum(len(columns) for columns in layers.values()),
        "columns_by_layer": {name: len(columns) for name, columns in layers.items()},
    }


def _external() -> dict[str, int]:
    out = {}
    for path in sorted(paths.EXTERNAL.glob("*.csv")):
        with path.open(encoding="utf-8") as handle:
            out[path.stem] = sum(1 for _ in handle) - 1
    return out


def _fixture() -> dict[str, Any]:
    import pandas as pd

    sample = pd.read_parquet(paths.FIXTURES / "vra_sample.parquet", columns=["route", "year"])
    return {
        "legs": len(sample),
        "routes": int(sample["route"].nunique()),
        "years": sorted(
            int(y) for y in sample["year"].dropna().unique() if y in {2004, 2009, 2012}
        ),
    }


def _decisions() -> dict[str, Any]:
    text = (paths.REPO_ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    return {"n_adrs": len(re.findall(r"^## ADR-\d{4}", text, flags=re.MULTILINE))}


def build(previous: dict[str, Any] | None = None) -> dict[str, Any]:
    """Every headline number, read from the artefacts under `root`."""
    if previous is None and SUMMARY_PATH.exists():
        previous = _json(SUMMARY_PATH)
    previous = previous or {}
    summary = {
        "reconstruction": _reconstruction(previous),
        "article_panel": _article_panel(),
        "published": _published(),
        "estimation": _estimation(),
        "prediction": _prediction(),
        "theory": _theory(),
        "registry": _registry(),
        "external": _external(),
        "fixture": _fixture(),
        "decisions": _decisions(),
    }
    summary["meta"] = {
        "generated_by": "airline-delays summary",
        "git_commit": git_commit(paths.REPO_ROOT, short=True),
        "inputs": [
            "data/raw/manifest.json",
            "data/staged/manifest.json (when present)",
            "data/analysis/manifest.json",
            "data/analysis/panel_manifest.json",
            "data/analysis/article_panel_manifest.json",
            "data/analysis/*.parquet",
            "src/airline_delays/estimation/published.json",
            "reports/replication/{summary,results}.json",
            "reports/prediction/{dataset,rolling,fixed,leakage}.json",
            "reports/theory/{model,figures}.json",
            "data/external/*.csv",
            "tests/fixtures/vra_sample.parquet",
            "DECISIONS.md",
        ],
        "note": "No timestamp on purpose: a rerun on an unchanged tree changes nothing but meta.",
    }
    return summary


def write(path: Path = SUMMARY_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def check(path: Path = SUMMARY_PATH) -> list[str]:
    """Differences between the committed summary and a rebuild, ignoring `meta`."""
    if not path.exists():
        return [f"{path} does not exist; run `airline-delays summary`"]
    committed = _json(path)
    fresh = build(previous=committed)
    committed.pop("meta", None)
    fresh.pop("meta", None)
    problems = []
    for key in sorted(set(committed) | set(fresh)):
        if committed.get(key) != fresh.get(key):
            problems.append(f"{key}: committed value differs from a rebuild")
    return problems
