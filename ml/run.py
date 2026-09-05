"""Run the whole prediction phase and write `reports/prediction/`.

Outputs, all under ``reports/prediction/``:

``rolling.json``
    The headline (ADR-0009): one entry per test year 2006-2013, both horizons,
    both naive baselines, on every test row and again on the subset with a
    linked inbound leg.
``fixed.json``
    The illustrative split 2002-2010 / 2011 / 2012-2013, for the four binary
    targets.
``calibration.json``
    The calibration table of every rolling fold and horizon.
``importance.json``
    Permutation importance and total gain on the last rolling fold.
``dataset.json``
    Per-year accounting: rows, the ADR-0017 reading-B counts (flights read as
    "no alteration reported" and flights left out of scope), the ADR-0015
    suspect exclusion, base rates, and the share of flights with a linked
    inbound leg whose arrival is readable.
``rolling_reading_A.json``
    The same headline run under the superseded reading A, kept so the
    sensitivity block in ``results.md`` can print both. Not regenerated.
``leakage.json``
    `ml.leakage_tests` run against the real dataset, not only the fixture.
``results.md``
    The same content as Markdown. `reports/prediction.typ` reads the JSON, so
    no number in the report is typed by hand.

Usage::

    uv run python -m ml.run                     # everything, about 30 minutes
    uv run python -m ml.run --rebuild           # rebuild the dataset first
    uv run python -m ml.run --test-years 2012,2013 --skip-fixed
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from ml import dataset_flights as ds
from ml import evaluate as ev
from ml import leakage_tests as lk
from ml import split as sp
from ml import train_xgb as tx

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / "prediction"

READING_A_NAME = "rolling_reading_A.json"
"""The rolling-origin run made before ADR-0017, kept for the sensitivity block.

Reading A treated an empty actual time as unknown, so a pre-2010 target existed
only for the flights that had an *occurrence* and 75-94% of them were late. The
file is a copy of that run's `rolling.json`, not a re-estimate: the models are
not retrained under a superseded reading, and the block says which numbers are
comparable (the 2010-2013 folds, where the two readings coincide) and which are
not (2006-2009, where the population itself changes).
"""

MAIN_TARGET = "late15_arr"
FIXED_TARGETS: tuple[str, ...] = ("late15_arr", "late30_arr", "late15_dep", "cancelled")
TARGET_LABEL: dict[str, str] = {
    "late15_arr": "arrival more than 15 minutes late",
    "late30_arr": "arrival more than 30 minutes late",
    "late15_dep": "departure more than 15 minutes late",
    "cancelled": "flight cancelled",
}
UNFILTERED_TARGETS: frozenset[str] = frozenset({"cancelled"})
"""Targets defined on every scheduled row, so no ADR-0012 exclusion applies."""


# --------------------------------------------------------------------- one fold


def run_fold(
    fold: sp.Fold,
    *,
    target: str,
    horizons: tuple[str, ...],
    dataset_dir: Path,
    learner: str,
    sample_rate: float,
    jobs: int,
    calibrate: bool,
    keep_models: bool = False,
) -> dict[str, Any]:
    """Train, score and describe one fold, for every horizon asked for."""
    started = time.time()
    require = target not in UNFILTERED_TARGETS
    frames = {
        part: sp.load_years(
            years,
            target,
            ds.FEATURES_H1,
            dataset_dir=dataset_dir,
            extra=("prev_leg",),
            sample_rate=sample_rate if part == "train" else 1.0,
            require_target=require,
        )
        for part, years in (
            ("train", fold.train_years),
            ("valid", (fold.valid_year,)),
            ("test", fold.test_years),
        )
    }
    train_frame, valid_frame, test_frame = ds.align_categories(
        [frames["train"], frames["valid"], frames["test"]]
    )
    y_test = test_frame[target].to_numpy(dtype="float64")
    linked = (test_frame["prev_leg"] == 1).to_numpy()
    base_rate_train = float(train_frame[target].mean())
    entry: dict[str, Any] = {
        **fold.as_dict(),
        "target": target,
        "n_train": len(train_frame),
        "n_valid": len(valid_frame),
        "n_test": len(test_frame),
        "base_rate_train": base_rate_train,
        "base_rate_test": float(y_test.mean()),
        "linked_share_test": float(linked.mean()),
        "sample_rate": sample_rate,
        "models": {},
        "linked_subset": {},
        "calibration": {},
    }
    fitted: dict[str, tx.Fitted] = {}
    for horizon in horizons:
        model = tx.train(
            train_frame,
            valid_frame,
            horizon=horizon,
            target=target,
            learner=learner,
            n_jobs=jobs,
        )
        predicted = model.predict(test_frame)
        entry["models"][horizon] = {
            **model.as_dict(),
            **ev.binary_metrics(y_test, predicted),
        }
        entry["linked_subset"][horizon] = ev.binary_metrics(y_test[linked], predicted[linked])
        if calibrate:
            entry["calibration"][horizon] = ev.calibration_table(y_test, predicted)
        fitted[horizon] = model
        print(
            f"  {fold.name} {target} {horizon}: "
            f"AUC {_show(entry['models'][horizon]['auc'])} "
            f"PR {_show(entry['models'][horizon]['pr_auc'])} "
            f"Brier {_show(entry['models'][horizon]['brier'])} "
            f"({model.seconds:.0f}s, {model.best_iteration} trees)",
            flush=True,
        )
    baselines = ev.naive_predictions(test_frame, base_rate_train)
    entry["baselines"] = {
        name: {
            **ev.binary_metrics(y_test, values),
            "linked_subset": ev.binary_metrics(y_test[linked], values[linked]),
        }
        for name, values in baselines.items()
    }
    entry["seconds"] = round(time.time() - started, 1)
    if keep_models:
        entry["_fitted"] = fitted
        entry["_test"] = test_frame
    return entry


def _show(value: float | None) -> str:
    return "   n/a" if value is None else f"{value:.4f}"


# ------------------------------------------------------------------------- run


def run(
    *,
    dataset_dir: Path = ds.DATASET_DIR,
    out_dir: Path = REPORT_DIR,
    test_years: tuple[int, ...] = sp.ROLLING_TEST_YEARS,
    horizons: tuple[str, ...] = ("D-1", "H-1"),
    learner: str = "xgboost",
    sample_rate: float = 1.0,
    jobs: int = 8,
    skip_fixed: bool = False,
    permutation: bool = True,
) -> dict[str, Any]:
    """The whole evaluation, written to `out_dir`."""
    started = time.time()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = _dataset_manifest(dataset_dir)
    _write(out_dir / "dataset.json", manifest)
    _write(out_dir / "leakage.json", _leakage(dataset_dir, manifest))

    folds = sp.rolling_origin(test_years=test_years)
    rolling: list[dict[str, Any]] = []
    last_models: dict[str, tx.Fitted] = {}
    last_test = None
    for position, fold in enumerate(folds):
        keep = permutation and position == len(folds) - 1
        entry = run_fold(
            fold,
            target=MAIN_TARGET,
            horizons=horizons,
            dataset_dir=dataset_dir,
            learner=learner,
            sample_rate=sample_rate,
            jobs=jobs,
            calibrate=True,
            keep_models=keep,
        )
        if keep:
            last_models = entry.pop("_fitted")
            last_test = entry.pop("_test")
        rolling.append(entry)
    calibration = {entry["name"]: entry.pop("calibration") for entry in rolling}
    rolling_doc = {
        "meta": _meta(learner, sample_rate, horizons, started),
        "target": MAIN_TARGET,
        "target_label": TARGET_LABEL[MAIN_TARGET],
        "folds": rolling,
    }
    _write(out_dir / "rolling.json", rolling_doc)
    _write(out_dir / "calibration.json", calibration)

    importance: dict[str, Any] = {}
    if permutation and last_models and last_test is not None:
        for horizon, model in last_models.items():
            importance[horizon] = ev.permutation_importance(model, last_test, MAIN_TARGET)
            print(f"  permutation importance {horizon}: {len(importance[horizon])} features")
        _write(
            out_dir / "importance.json",
            {
                "fold": folds[-1].name,
                "target": MAIN_TARGET,
                "repeats": ev.PERMUTATION_REPEATS,
                "sample": min(ev.PERMUTATION_SAMPLE, len(last_test)),
                "horizons": importance,
            },
        )

    fixed_doc: dict[str, Any] = {}
    if not skip_fixed:
        fold = sp.fixed_split()
        entries = [
            run_fold(
                fold,
                target=target,
                horizons=horizons,
                dataset_dir=dataset_dir,
                learner=learner,
                sample_rate=sample_rate,
                jobs=jobs,
                calibrate=False,
            )
            for target in FIXED_TARGETS
        ]
        for entry in entries:
            entry.pop("calibration", None)
        fixed_doc = {
            "meta": _meta(learner, sample_rate, horizons, started),
            "labels": TARGET_LABEL,
            "folds": entries,
        }
        _write(out_dir / "fixed.json", fixed_doc)

    markdown = write_markdown(rolling_doc, fixed_doc, importance, manifest, out_dir)
    print(f"\nprediction: {markdown} ({time.time() - started:.0f}s)")
    return {"rolling": rolling_doc, "fixed": fixed_doc, "importance": importance}


def _meta(
    learner: str, sample_rate: float, horizons: tuple[str, ...], started: float
) -> dict[str, Any]:
    from vra import stage as stage_mod

    return {
        "learner": learner,
        "sample_rate": sample_rate,
        "horizons": list(horizons),
        "horizon_labels": tx.HORIZON_LABEL,
        "params": {
            key: value
            for key, value in tx.DEFAULT_PARAMS.items()
            if key not in {"objective", "eval_metric"}
        },
        "early_stopping_rounds": tx.EARLY_STOPPING_ROUNDS,
        "git_commit": stage_mod.git_commit(REPO_ROOT, short=True),
        "tool_versions": stage_mod.tool_versions(),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "seconds": round(time.time() - started, 1),
    }


def _dataset_manifest(dataset_dir: Path) -> dict[str, Any]:
    path = Path(dataset_dir) / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing; run `just ml` or `--rebuild`")
    return json.loads(path.read_text(encoding="utf-8"))


def _leakage(dataset_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Run the leakage checks against the real dataset, not only the fixture.

    Two years, the build's first and its last: the first because the busy-hour
    check asks that a window which has not opened yet be empty, the last because
    it is the year the headline fold predicts. Everything in between is the same
    code path over the same joins.
    """
    import pandas as pd

    from vra import features as features_mod
    from vra import stage as stage_mod

    years = (int(manifest["by_year"][0]["year"]), int(manifest["by_year"][-1]["year"]))
    frame = ds.read_dataset(dataset_dir, years=years)
    fact = pd.read_parquet(ds.FACT_PATH)
    # The staged rows of those *calendar years*, not of those directories
    # (ADR-0016): the movement recount has to see exactly the rows the dataset
    # saw, or a leg scheduled for 1 January and filed in the December file
    # shows up as a disagreement the pipeline does not have.
    con = stage_mod.connect()
    try:
        staged = pd.concat(
            [
                con.execute(
                    "SELECT origin_icao, dest_icao, sched_dep, sched_arr FROM "
                    + features_mod.year_source_sql(ds.STAGED_DIR, year)
                ).df()
                for year in years
            ],
            ignore_index=True,
        )
    finally:
        con.close()
    checks = lk.run_all(frame, fact, staged)
    lk.assert_all(checks)
    return {"years": list(years), "rows": len(frame), "checks": lk.as_records(checks)}


def _write(path: Path, payload: Any) -> Path:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# -------------------------------------------------------------------- markdown


def write_markdown(
    rolling: dict[str, Any],
    fixed: dict[str, Any],
    importance: dict[str, Any],
    manifest: dict[str, Any],
    out_dir: Path,
) -> Path:
    """`results.md`: the same numbers as the JSON, in a table a human reads."""
    lines: list[str] = [
        "# Flight-level delay prediction - results",
        "",
        (
            f"Generated by `uv run python -m ml.run` ({rolling['meta']['generated_at']}, "
            f"commit `{rolling['meta']['git_commit']}`). Target: "
            f"`{rolling['target']}` ({rolling['target_label']})."
        ),
        "",
        "## Rolling origin (headline, ADR-0009)",
        "",
        "Train up to `y-2`, early-stop on `y-1`, test on `y`. `base` is the share of",
        "test rows that are positive; the two baselines are the previous month's",
        "prevalence for the route and for the airline group (ADR-0009).",
        "",
        (
            "| test year | n test | base | D-1 AUC | D-1 PR | D-1 Brier | H-1 AUC | H-1 PR |"
            " H-1 Brier | route AUC | route Brier | group AUC | group Brier |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for entry in rolling["folds"]:
        d1 = entry["models"].get("D-1", {})
        h1 = entry["models"].get("H-1", {})
        route = entry["baselines"]["route_prevalence_l1"]
        group = entry["baselines"]["group_prevalence_l1"]
        lines.append(
            f"| {entry['test_years'][0]} | {entry['n_test']:,d} | "
            f"{_num(entry['base_rate_test'], 3)} | "
            f"{_num(d1.get('auc'))} | {_num(d1.get('pr_auc'))} | {_num(d1.get('brier'))} | "
            f"{_num(h1.get('auc'))} | {_num(h1.get('pr_auc'))} | {_num(h1.get('brier'))} | "
            f"{_num(route.get('auc'))} | {_num(route.get('brier'))} | "
            f"{_num(group.get('auc'))} | {_num(group.get('brier'))} |"
        )
    lines += [
        "",
        "### On the subset with a linked inbound leg",
        "",
        "The H-1 horizon only says anything where the inbound leg exists. Both",
        "horizons are re-scored on exactly those rows, so the difference is the",
        "horizon and not the population.",
        "",
        "| test year | linked share | n linked | D-1 AUC | H-1 AUC | D-1 Brier | H-1 Brier |",
        "|---|---|---|---|---|---|---|",
    ]
    for entry in rolling["folds"]:
        d1 = entry["linked_subset"].get("D-1", {})
        h1 = entry["linked_subset"].get("H-1", {})
        lines.append(
            f"| {entry['test_years'][0]} | {_num(entry['linked_share_test'], 3)} | "
            f"{d1.get('n', 0):,d} | {_num(d1.get('auc'))} | {_num(h1.get('auc'))} | "
            f"{_num(d1.get('brier'))} | {_num(h1.get('brier'))} |"
        )
    if fixed:
        lines += [
            "",
            "## Fixed split (illustrative)",
            "",
            "Train 2002-2010, validate 2011, test 2012-2013.",
            "",
            (
                "| target | n test | base | D-1 AUC | D-1 PR | D-1 Brier | H-1 AUC | H-1 PR |"
                " H-1 Brier |"
            ),
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for entry in fixed["folds"]:
            d1 = entry["models"].get("D-1", {})
            h1 = entry["models"].get("H-1", {})
            lines.append(
                f"| `{entry['target']}` | {entry['n_test']:,d} | "
                f"{_num(entry['base_rate_test'], 3)} | "
                f"{_num(d1.get('auc'))} | {_num(d1.get('pr_auc'))} | {_num(d1.get('brier'))} | "
                f"{_num(h1.get('auc'))} | {_num(h1.get('pr_auc'))} | {_num(h1.get('brier'))} |"
            )
    for horizon, rows in importance.items():
        lines += [
            "",
            f"## Permutation importance, {rolling['folds'][-1]['name']}, {horizon}",
            "",
            "Drop in test AUC when the column is shuffled, mean of 3 repeats.",
            "",
            "| feature | AUC drop | sd | total gain |",
            "|---|---|---|---|",
        ]
        for row in rows[:15]:
            lines.append(
                f"| `{row['feature']}` | {_num(row['auc_drop'], 4)} | "
                f"{_num(row['auc_drop_sd'], 4)} | {row['total_gain']:,.0f} |"
            )
    lines += _reading_sensitivity(rolling, out_dir)
    lines += [
        "",
        "## Dataset (ADR-0017 accounting)",
        "",
        "`target rows` are the realised flights whose arrival outcome is readable:",
        "an actual arrival time, or — before 2010, for a carrier whose `groups.csv`",
        "class is FSC, LCC or regional — an empty one, which under IAC 1504 means no",
        "alteration was reported (`no alteration`, the `on_time_no_bav` flag).",
        "`out of scope` are realised flights the rule does not cover: `other` and",
        "unlabelled carriers, mostly foreign operators and the non-operating side of",
        "a code-share, whose empty actual time stays unknown. `suspect` is the",
        "ADR-0015 exclusion: an actual timestamp a whole day or more from the",
        "schedule. `prev known` is the share of *linked* flights whose inbound leg's",
        "arrival is readable — what the H-1 horizon actually has to work with.",
        "",
        (
            "| year | flights | realised | target rows | no alteration | share of realised |"
            " out of scope | suspect | late15 rate | cancelled rate | linked | prev known |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in manifest["by_year"]:
        lines.append(
            f"| {row['year']} | {row['rows']:,d} | {row['realized']:,d} | "
            f"{row['target_rows']:,d} | {row.get('on_time_no_bav', 0):,d} | "
            f"{_num(row.get('on_time_no_bav_share'), 3)} | "
            f"{row['target_excluded_missing_actual']:,d} | "
            f"{row['target_excluded_suspect']:,d} | "
            f"{_num(row['late15_arr_rate'], 3)} | {_num(row['cancelled_rate'], 3)} | "
            f"{_num(row['prev_leg_share'], 3)} | {_num(row.get('prev_arr_known_share'), 3)} |"
        )
    lines.append("")
    path = Path(out_dir) / "results.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _reading_sensitivity(rolling: dict[str, Any], out_dir: Path) -> list[str]:
    """The headline metrics under reading A next to reading B (ADR-0017).

    Reading A is read from the preserved `rolling_reading_A.json`; nothing is
    retrained. The comparison is only *like for like* from 2010 on, where the
    layout writes an actual time on every realised flight and the two readings
    are the same data — which is exactly what makes the 2006-2009 rows worth
    printing: the base rate falls from 88-94% to 18-30% because the population
    changes, not because a model improved.
    """
    path = Path(out_dir) / READING_A_NAME
    if not path.exists():
        return []
    previous = json.loads(path.read_text(encoding="utf-8"))
    before = {entry["test_years"][0]: entry for entry in previous.get("folds", [])}
    if not before:
        return []
    lines = [
        "",
        "## Sensitivity: reading A against reading B (ADR-0017)",
        "",
        "Reading A (superseded) treated an empty actual time on a realised flight as",
        "*unknown*, so before 2010 a target existed only for the flights that had an",
        "occurrence and 75-94% of them were late. Reading B reads the same empty field",
        "as *no alteration reported*. The A columns are the previous run, kept in",
        f"`reports/prediction/{READING_A_NAME}`; they are not re-estimated.",
        "",
        "From 2010 the two readings see the same data, so those rows are a like-for-like",
        "comparison of the pipeline. Before 2010 they are not: the test population itself",
        "differs, and the base rate says so.",
        "",
        (
            "| test year | n test A | n test B | base A | base B | D-1 AUC A | D-1 AUC B |"
            " H-1 AUC A | H-1 AUC B | D-1 Brier A | D-1 Brier B |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for entry in rolling["folds"]:
        year = entry["test_years"][0]
        old = before.get(year)
        if old is None:
            continue
        new_d1, new_h1 = entry["models"].get("D-1", {}), entry["models"].get("H-1", {})
        old_d1, old_h1 = old["models"].get("D-1", {}), old["models"].get("H-1", {})
        lines.append(
            f"| {year} | {old['n_test']:,d} | {entry['n_test']:,d} | "
            f"{_num(old['base_rate_test'], 3)} | {_num(entry['base_rate_test'], 3)} | "
            f"{_num(old_d1.get('auc'))} | {_num(new_d1.get('auc'))} | "
            f"{_num(old_h1.get('auc'))} | {_num(new_h1.get('auc'))} | "
            f"{_num(old_d1.get('brier'))} | {_num(new_d1.get('brier'))} |"
        )
    return lines


def _num(value: Any, digits: int = 4) -> str:
    if value is None:
        return "--"
    return f"{float(value):.{digits}f}"


# ------------------------------------------------------------------------ main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--rebuild", action="store_true", help="rebuild data/derived/ml first")
    parser.add_argument("--dataset-dir", type=Path, default=ds.DATASET_DIR)
    parser.add_argument("--out", type=Path, default=REPORT_DIR)
    parser.add_argument(
        "--test-years",
        default=",".join(str(year) for year in sp.ROLLING_TEST_YEARS),
        help="comma-separated rolling-origin test years",
    )
    parser.add_argument("--horizons", default="D-1,H-1")
    parser.add_argument("--learner", default="xgboost", choices=list(tx.LEARNERS))
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=1.0,
        help="keep this share of route hash buckets in training (1.0 = everything)",
    )
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--skip-fixed", action="store_true")
    parser.add_argument("--no-permutation", action="store_true")
    args = parser.parse_args(argv)

    if args.rebuild:
        result = ds.build_dataset(out_dir=args.dataset_dir)
        print(f"dataset: {result.rows:,d} rows in {result.seconds:.0f}s -> {result.out_dir}")
    run(
        dataset_dir=args.dataset_dir,
        out_dir=args.out,
        test_years=tuple(int(year) for year in args.test_years.split(",")),
        horizons=tuple(part.strip() for part in args.horizons.split(",")),
        learner=args.learner,
        sample_rate=args.sample_rate,
        jobs=args.jobs,
        skip_fixed=args.skip_fixed,
        permutation=not args.no_permutation,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
