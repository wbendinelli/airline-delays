"""Sample, specification and estimation machinery shared by Tables 2-7.

Everything that the published do-files fix once and reuse in every table lives
here: where the panel comes from (:class:`Source`), the sample filters, the
regressor and instrument lists, the fixed-effect and seasonality dummies, the
HAC settings, and the single estimation entry point :func:`fit`.

Two sources, one code path
--------------------------
``Source.PRIVATE``
    The authors' final panel, ``proj18.dta``, reached only through
    ``AIRLINE_DELAYS_PRIVATE_DIR`` (never copied into this repository, never
    committed -- see ``CLAUDE.md`` and ``SECURITY.md``). This is the benchmark:
    it is the base the published tables were produced from, so a difference
    against it is a difference in *our* econometrics, not in the data.
``Source.PUBLIC``
    ``data/analysis/panel_route_month.parquet``, rebuilt from ANAC's raw VRA by
    this repository. Point ``AIRLINE_DELAYS_PANEL`` at a panel file, or leave it
    at the default path, and pass ``--source public``. If the file is not there
    at all, :class:`PublicPanelNotBuilt` names the path and the command that
    builds it.

The public panel contract is :data:`REQUIRED_COLUMNS` -- the article's own
variable names, because this module is a port of a Stata specification and
those names are what identify each regressor in the published tables. A panel
that carries a column under a different *name* is fine (:data:`PUBLIC_ALIASES`,
and regions are looked up from node codes); a panel that carries something
*near* a published variable is not, and the column counts as missing. Whatever
is absent is recorded in ``attrs["missing_contract_columns"]``, reported in the
sample filters, and named by :class:`PublicPanelIncomplete` the moment a table
actually needs it -- so the public run estimates what it can and says, in
writing, what it cannot. A proxy is never promoted into a published variable's
place; that is the substitution ``CLAUDE.md`` forbids.

Estimation choices, and why
---------------------------
* **Bandwidth 4, Bartlett.** ``linearmodels`` weights lag *j* by
  ``1 - j/(bandwidth+1)``; Stata's ``ivreg2 ..., bw(5)`` weights it by
  ``1 - j/5`` for ``j = 0..4``. **4 here is 5 there.** The article's own choice
  is ``T^(1/3)`` with ``T = 144``, i.e. 5.24 -> 5.
* **``debiased=True``.** ``ivreg2`` without ``small`` divides by N; with
  ``small`` it divides by N-K and prints an F statistic. The published tables
  print an F statistic, so ``small`` was on.
* **Seasonality dummies on.** ``dummymonthreg`` builds the 60 region x month
  dummies but they never appear in ``gregcontrols``; the ``.ado`` that would
  settle it was not delivered. The article says "a fixed-effects procedure with
  seasonality controls", and including them puts the coefficients measurably
  closer to the published ones, so they are in. The switch stays exposed
  (``with_seasonality``) and ``src/airline_delays/estimation/sensitivity.py`` reports both.
* **Dummies enter explicitly.** The do-files use neither ``partial()`` nor
  ``xtivreg2``, so the 189 surviving route dummies and ``t_2..t_144`` are
  columns of the design matrix, with one route dummy omitted against the
  constant and exact collinearity removed by a rank-revealing QR.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
import scipy.linalg as sla
from scipy import stats as _stats

from airline_delays import paths
from airline_delays.estimation import kp as kpmod

REPO_ROOT = paths.REPO_ROOT
PRIVATE_DIR_VAR = "AIRLINE_DELAYS_PRIVATE_DIR"
PANEL_PATH_VAR = "AIRLINE_DELAYS_PANEL"
PUBLIC_PANEL_PATH = REPO_ROOT / "data" / "analysis" / "panel_route_month.parquet"
PRIVATE_PANEL_RELATIVE = Path("Base de dados final") / "proj18.dta"

Estimator = Literal["gmm2s", "liml", "ols"]


class Source(str, Enum):
    """Where the route-month panel comes from."""

    PRIVATE = "private"
    PUBLIC = "public"


class PublicPanelNotBuilt(FileNotFoundError):
    """The public panel has not been produced yet."""


class PublicPanelIncomplete(ValueError):
    """The public panel exists but does not carry every column the tables need."""


class PrivateSourceUnavailable(FileNotFoundError):
    """`AIRLINE_DELAYS_PRIVATE_DIR` is unset, or does not hold the benchmark panel."""


# ------------------------------------------------------------------ the model
EXOG_PARTIAL: tuple[str, ...] = (
    "maxprdel",
    "prwheather",
    "princident",
    "pr_connc",
    "cshare",
    "dailyflcong",
    "dailyflncong",
)
LCC_TERMS: tuple[str, ...] = ("lcc", "maxalccfu")
EXOG_FULL: tuple[str, ...] = EXOG_PARTIAL + LCC_TERMS
ENDOG: tuple[str, ...] = ("rthhi", "maxcthhi")

#: `gregins` for the ODDS/ODDSD blocks (5 excluded instruments, J with 3 df).
INSTRUMENTS_ODDS: tuple[str, ...] = (
    "h3_maxcthhi",
    "lnh1_maxcthhi",
    "l1h1_maxcthhi",
    "l1h2_maxcthhi",
    "h2_rthhi",
)
#: `gregins` for the MINS/MINSD blocks (3 excluded instruments, J with 1 df).
#: The two lists differ, the article does not say why, and they are not unified
#: here -- see `docs/notes/replication.md`.
INSTRUMENTS_MINS: tuple[str, ...] = ("h1_maxcthhi", "h2_maxcthhi", "h3_maxcthhi")

ARRIVAL_REGRESSANDS: tuple[str, ...] = ("fsc_oddsarr", "fsc_minsarr", "fsc_minsp15arr")
DEPARTURE_REGRESSANDS: tuple[str, ...] = ("fsc_oddsdep", "fsc_minsdep", "fsc_minsp15dep")

#: Region codes of the `sz_*` dummies -> the region names carried by the panel.
REGIONS: dict[str, str] = {
    "ne": "Nordeste",
    "no": "Norte",
    "co": "Centro-Oeste",
    "se": "Sudeste",
    "su": "Sul",
}
SEASONALITY: tuple[str, ...] = tuple(
    f"sz_{code}_m_{month}" for code in REGIONS for month in range(1, 13)
)
FIRST_YM = 200201
LAST_YM = 201312
N_PERIODS = 144
TIME_DUMMIES: tuple[str, ...] = tuple(f"t_{i}" for i in range(1, N_PERIODS + 1))

#: Accepted spellings of a contract column in a public panel. Only synonyms --
#: two names for the same quantity -- ever go here. A column that measures
#: something *near* the article's variable (a proxy, a different denominator) is
#: a missing column, not an alias; mapping one in would be adjusting a
#: definition to make numbers appear, which `CLAUDE.md` forbids outright.
PUBLIC_ALIASES: dict[str, tuple[str, ...]] = {
    "od": ("od", "route"),
    "o_region": ("o_region",),
    "d_region": ("d_region",),
}

#: Brazil's five macro-regions by state, used only to rebuild the `sz_*`
#: seasonality dummies when a panel carries node codes instead of regions.
#: Source: IBGE's Divisao Regional do Brasil.
UF_REGION: dict[str, str] = {
    "AC": "Norte",
    "AP": "Norte",
    "AM": "Norte",
    "PA": "Norte",
    "RO": "Norte",
    "RR": "Norte",
    "TO": "Norte",
    "AL": "Nordeste",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "MA": "Nordeste",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste",
    "GO": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste",
    "MG": "Sudeste",
    "RJ": "Sudeste",
    "SP": "Sudeste",
    "PR": "Sul",
    "RS": "Sul",
    "SC": "Sul",
}
NODES_CSV = REPO_ROOT / "data" / "external" / "nodes.csv"

KEY_COLUMNS: tuple[str, ...] = ("od", "ym", "o_region", "d_region")
ALL_INSTRUMENTS: tuple[str, ...] = tuple(sorted(set(INSTRUMENTS_ODDS + INSTRUMENTS_MINS)))
REQUIRED_COLUMNS: tuple[str, ...] = (
    KEY_COLUMNS + ARRIVAL_REGRESSANDS + DEPARTURE_REGRESSANDS + EXOG_FULL + ENDOG + ALL_INSTRUMENTS
)

#: The order the article lists coefficients in, and the labels it prints.
COEF_ORDER: tuple[str, ...] = (
    "dailyflcong",
    "dailyflncong",
    "prwheather",
    "princident",
    "pr_connc",
    "maxprdel",
    "cshare",
    "rthhi",
    "maxcthhi",
    "lcc",
    "maxalccfu",
)
COEF_LABEL: dict[str, str] = {
    "dailyflcong": "Nr flights in congested hours",
    "dailyflncong": "Nr flights in uncongested hours",
    "prwheather": "Prop flights with bad weather",
    "princident": "Prop flights with incidents",
    "pr_connc": "Prop flights held for late connections",
    "maxprdel": "Max prop city delayed flights",
    "cshare": "Codeshare agreement",
    "rthhi": "HHI city-pair",
    "maxcthhi": "HHI max endpoint cities",
    "lcc": "LCC presence city-pair",
    "maxalccfu": "LCC presence max endpoint cities",
}

# ------------------------------------------------------------- HAC / estimator
HAC_BANDWIDTH = 4
DEBIASED = True
WITH_SEASONALITY = True
SINGLETON_CUTOFF = 5

#: ADR-0008. The default threshold trims flight-level delays at 313.25 minutes;
#: 117.10 is the arrival-side alternative the laboratory also used, and ``None``
#: means no trimming. A panel that offers a threshold other than the default
#: exposes it as a suffixed regressand -- see :func:`regressand_column`.
DEFAULT_OUTLIER_THRESHOLD = 313.25
OUTLIER_THRESHOLDS: tuple[float | None, ...] = (313.25, 117.10, None)


def regressand_column(base: str, threshold: float | None = DEFAULT_OUTLIER_THRESHOLD) -> str:
    """Name of the regressand built under `threshold` (ADR-0008).

    The default threshold is the panel's own canonical column; every other
    threshold is a suffixed variant, e.g. ``fsc_oddsarr__out11710`` and
    ``fsc_oddsarr__outnone``. A source that does not carry the variant simply
    does not have that row of the sensitivity table -- it is reported as
    unavailable, never silently substituted.
    """
    if threshold == DEFAULT_OUTLIER_THRESHOLD:
        return base
    tag = "none" if threshold is None else f"{threshold:.2f}".replace(".", "")
    return f"{base}__out{tag}"


# --------------------------------------------------------------- loading, once
_PANEL_CACHE: dict[tuple[Source, str], pd.DataFrame] = {}


def private_dir() -> Path:
    """The private benchmark directory, from the environment. Never hard-coded."""
    raw = os.environ.get(PRIVATE_DIR_VAR)
    if not raw:
        raise PrivateSourceUnavailable(
            f"{PRIVATE_DIR_VAR} is unset; private mode reads the benchmark panel only "
            "through that variable (CLAUDE.md, SECURITY.md)"
        )
    path = Path(raw).expanduser()
    if not path.is_dir():
        raise PrivateSourceUnavailable(f"{PRIVATE_DIR_VAR}={path} is not a directory")
    return path


def public_panel_path() -> Path:
    """Where the public panel is expected; ``AIRLINE_DELAYS_PANEL`` overrides it."""
    override = os.environ.get(PANEL_PATH_VAR)
    return Path(override).expanduser() if override else PUBLIC_PANEL_PATH


def _load_private() -> pd.DataFrame:
    directory = private_dir()
    dta = directory / PRIVATE_PANEL_RELATIVE
    if not dta.exists():
        raise PrivateSourceUnavailable(
            f"{dta} not found; the benchmark panel is expected at "
            f"<{PRIVATE_DIR_VAR}>/{PRIVATE_PANEL_RELATIVE}"
        )
    frame = pd.read_stata(dta, columns=list(REQUIRED_COLUMNS), convert_categoricals=False)
    frame["ym"] = frame["ym"].astype(int)
    return frame


def _load_public() -> pd.DataFrame:
    path = public_panel_path()
    if not path.exists():
        raise PublicPanelNotBuilt(
            f"the public route-month panel is not built yet: {path} does not exist. "
            "Build it with `just panel` (see ROADMAP.md), point "
            f"{PANEL_PATH_VAR} at an existing panel file, or run this table with "
            "`--source private` and AIRLINE_DELAYS_PRIVATE_DIR set."
        )
    frame = pd.read_parquet(path)
    for canonical, spellings in PUBLIC_ALIASES.items():
        if canonical in frame.columns:
            continue
        found = next((name for name in spellings if name in frame.columns), None)
        if found is not None:
            frame = frame.rename(columns={found: canonical})
    frame = _add_regions(frame)
    for name in ("od", "ym"):
        if name not in frame.columns:
            raise PublicPanelIncomplete(
                f"{path} has no {name!r} column and no accepted synonym "
                f"({', '.join(PUBLIC_ALIASES.get(name, (name,)))}); without it the panel cannot "
                "be read as a route-month panel at all. The full contract is "
                "replication.common.REQUIRED_COLUMNS."
            )
    keep = [name for name in REQUIRED_COLUMNS if name in frame.columns]
    missing = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
    frame = frame.loc[:, keep].copy()
    frame["ym"] = frame["ym"].astype(int)
    frame.attrs["missing_contract_columns"] = missing
    frame.attrs["panel_path"] = str(path)
    return frame


def _add_regions(frame: pd.DataFrame) -> pd.DataFrame:
    """Fill `o_region`/`d_region` from node codes when the panel carries nodes.

    The `sz_*` seasonality dummies are region x month, and a panel built from
    ANAC's raw data naturally carries airport or metropolitan node codes rather
    than macro-regions. `data/external/nodes.csv` maps node to state, and
    :data:`UF_REGION` maps state to region -- a lookup, not a redefinition.
    """
    if {"o_region", "d_region"} <= set(frame.columns):
        return frame
    if not ({"origin_node", "dest_node"} <= set(frame.columns) and NODES_CSV.exists()):
        return frame
    nodes = pd.read_csv(NODES_CSV, usecols=["node", "uf"]).drop_duplicates("node")
    lookup = {row.node: UF_REGION.get(row.uf) for row in nodes.itertuples()}
    frame = frame.copy()
    frame["o_region"] = frame["origin_node"].map(lookup)
    frame["d_region"] = frame["dest_node"].map(lookup)
    return frame


def load_panel(source: Source | str = Source.PRIVATE) -> pd.DataFrame:
    """The raw route-month panel, before any sample filter, with the dummies attached."""
    source = Source(source)
    key = (source, str(public_panel_path()) if source is Source.PUBLIC else "")
    if key in _PANEL_CACHE:
        return _PANEL_CACHE[key]
    frame = _load_private() if source is Source.PRIVATE else _load_public()
    attrs = dict(frame.attrs)
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = add_dummies(frame)
    frame.attrs.update(attrs)
    _PANEL_CACHE[key] = frame
    return frame


def add_dummies(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach ``t_1..t_144`` and the 60 ``sz_*`` region x month dummies.

    Both are rebuilt from ``ym``, ``o_region`` and ``d_region`` rather than read
    from the panel, so the public and private paths are identical. Verified
    against the 60 stored ``sz_*`` columns and the 144 stored ``t_*`` columns of
    ``proj18.dta``: exact agreement on all 24,589 rows.
    """
    frame = frame.copy()
    year, month = np.divmod(frame["ym"].to_numpy(dtype=np.int64), 100)
    period = (year - FIRST_YM // 100) * 12 + month
    frame["_period"] = period
    time_block = {
        name: (period == index).astype(np.float64)
        for index, name in enumerate(TIME_DUMMIES, start=1)
    }
    if {"o_region", "d_region"} <= set(frame.columns):
        origin = frame["o_region"].to_numpy()
        destination = frame["d_region"].to_numpy()
        season_block = {
            f"sz_{code}_m_{m}": (((origin == name) | (destination == name)) & (month == m)).astype(
                np.float64
            )
            for code, name in REGIONS.items()
            for m in range(1, 13)
        }
    else:
        # No regions in the panel: the dummies exist but are empty, and the QR in
        # `drop_collinear` removes them. Recorded, never silently substituted.
        season_block = {name: np.zeros(len(frame)) for name in SEASONALITY}
    return pd.concat([frame, pd.DataFrame(time_block | season_block, index=frame.index)], axis=1)


def build_sample(
    source: Source | str = Source.PRIVATE,
    *,
    filter_regressand: str = "fsc_oddsarr",
) -> pd.DataFrame:
    """The do-files' opening block, in the order they run it.

    ``projbase 18 ; drop fe_* ; drop sz_* ; drop if <y>==. ; findsingletons k ;
    drop if _count_k<=5 ; panelset ; effects k ; dummymonthreg``

    `filter_regressand` is ``fsc_oddsarr`` for Tables 2-6 and ``fsc_oddsdep``
    for Table 7. It bites in *every* column of a table, including the MINS
    columns whose own regressand is never missing: that is deliberate in the
    do-files, so all columns of a table share one sample. Reproduce it.
    """
    frame = load_panel(source)
    n_raw, routes_raw = len(frame), frame["od"].nunique()
    if filter_regressand not in frame.columns:
        raise PublicPanelIncomplete(
            f"the panel does not carry the sample filter {filter_regressand!r}; "
            f"missing from the contract: {frame.attrs.get('missing_contract_columns', [])}"
        )
    # The article's panel is 2002m1-2013m12. `projbase 18` already delivers that
    # window; a rebuilt panel may be wider, and rows outside it would carry an
    # all-zero row of time dummies and be absorbed by the constant.
    in_window = frame["ym"].between(FIRST_YM, LAST_YM)
    n_outside_window = int((~in_window).sum())
    frame = frame[in_window].copy()
    frame = frame[frame[filter_regressand].notna()].copy()
    n_after_missing = len(frame)
    counts = frame.groupby("od")["od"].transform("size")
    frame = frame[counts > SINGLETON_CUTOFF].copy()
    frame = frame.sort_values(["od", "ym"]).reset_index(drop=True)
    frame_missing = load_panel(source).attrs.get("missing_contract_columns", [])
    frame["_route_index"] = pd.factorize(frame["od"])[0]
    frame["_time_index"] = frame["_period"] - 1
    frame.attrs["filters"] = {
        "source": str(Source(source).value),
        "filter_regressand": filter_regressand,
        "n_raw": int(n_raw),
        "routes_raw": int(routes_raw),
        "n_outside_window": n_outside_window,
        "window": [FIRST_YM, LAST_YM],
        "missing_contract_columns": list(frame_missing),
        "n_after_missing_regressand": int(n_after_missing),
        "n_after_singleton_cut": len(frame),
        "routes": int(frame["od"].nunique()),
        "months": int(frame["ym"].nunique()),
        "singleton_cutoff": SINGLETON_CUTOFF,
    }
    return frame


# ---------------------------------------------------------------- design block
def route_dummies(frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """``effects k``: route dummies rebuilt on the restricted sample, first one omitted."""
    codes = frame["_route_index"].to_numpy()
    n_routes = int(codes.max()) + 1
    block = np.zeros((len(frame), n_routes), dtype=np.float64)
    block[np.arange(len(frame)), codes] = 1.0
    names = [f"fe_k_{i + 1}" for i in range(n_routes)]
    return block[:, 1:], names[1:]


def drop_collinear(
    matrix: np.ndarray, names: list[str], n_protected: int, tol: float = 1e-7
) -> tuple[np.ndarray, list[str], list[str]]:
    """Rank-revealing QR: drop a column that is a linear combination of earlier ones.

    ``ivreg2`` does this silently; NumPy does not. The first `n_protected`
    columns (constant and the regressors of interest) are never dropped. In
    these samples the cut is clean -- the null ``|R_jj|`` sit around 1e-10 and
    the smallest surviving one around 1e2.
    """
    scale = matrix.std(axis=0)
    scale[scale == 0] = 1.0
    upper = sla.qr(matrix / scale, mode="r", check_finite=False)[0]
    diagonal = np.abs(np.diag(upper))
    keep = diagonal > tol * diagonal.max()
    keep[:n_protected] = True
    dropped = [names[i] for i in range(len(names)) if not keep[i]]
    return matrix[:, keep], [names[i] for i in range(len(names)) if keep[i]], dropped


def design(
    frame: pd.DataFrame, exog: list[str], *, with_seasonality: bool
) -> tuple[np.ndarray, list[str], list[str]]:
    """``[const, exog, route dummies, t_2..t_144, (sz_*)]`` with collinear columns removed."""
    n = len(frame)
    blocks = [np.ones((n, 1)), frame[exog].to_numpy(np.float64)] if exog else [np.ones((n, 1))]
    names = ["const", *exog]
    dummies, dummy_names = route_dummies(frame)
    blocks.append(dummies)
    names += dummy_names
    time_columns = [name for name in TIME_DUMMIES[1:] if frame[name].to_numpy().any()]
    blocks.append(frame[time_columns].to_numpy(np.float64))
    names += time_columns
    if with_seasonality:
        blocks.append(frame[list(SEASONALITY)].to_numpy(np.float64))
        names += list(SEASONALITY)
    return drop_collinear(np.hstack(blocks), names, 1 + len(exog))


# ------------------------------------------------------------------ estimation
@dataclass(frozen=True)
class ColumnSpec:
    """One column of one published table."""

    column: int
    regressand: str
    exog: tuple[str, ...]
    endog: tuple[str, ...] = ()
    instruments: tuple[str, ...] = ()
    estimator: Estimator = "gmm2s"
    note: str = ""

    @property
    def is_iv(self) -> bool:
        return self.estimator != "ols" and bool(self.endog)


@dataclass
class ColumnResult:
    """Coefficients, standard errors and the statistics the article prints."""

    column: int
    regressand: str
    estimator: Estimator
    coefficients: dict[str, dict[str, float]]
    stats: dict[str, Any]
    dropped_collinear: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "column": self.column,
            "regressand": self.regressand,
            "estimator": self.estimator,
            "b": {name: values["b"] for name, values in self.coefficients.items()},
            "se": {name: values["se"] for name, values in self.coefficients.items()},
            "stats": self.stats,
            "n_dropped_collinear": len(self.dropped_collinear),
        }


def hansen_j(
    residuals: np.ndarray,
    instruments: np.ndarray,
    *,
    bandwidth: int = HAC_BANDWIDTH,
    panel: tuple[np.ndarray, np.ndarray] | None = None,
    n_params_overid: int,
) -> tuple[float, float, int]:
    """Hansen's J with the HAC optimal weight matrix, evaluated at given residuals.

    ``ivreg2`` prints this for every robust estimator, GMM or not, which is why
    Table 5 (LIML) reports a J barely different from Table 3's. ``linearmodels``
    exposes ``j_stat`` only on the GMM results, so LIML gets it from here.
    """
    moments = instruments * residuals[:, None]
    n = moments.shape[0]
    cov = kpmod.hac_moment_cov(moments, bandwidth, *(panel if panel else (None, None)))
    mean = moments.mean(axis=0)
    stat = float(n * mean @ np.linalg.pinv(cov) @ mean)
    df = int(n_params_overid)
    p = float(_stats.chi2.sf(stat, df)) if df > 0 else float("nan")
    return stat, p, df


def fit(
    sample: pd.DataFrame,
    spec: ColumnSpec,
    *,
    with_seasonality: bool = WITH_SEASONALITY,
    debiased: bool = DEBIASED,
    bandwidth: int = HAC_BANDWIDTH,
    outlier_threshold: float | None = DEFAULT_OUTLIER_THRESHOLD,
    panel_hac: bool = False,
) -> ColumnResult:
    """Estimate one column of one table and collect everything the article prints."""
    from linearmodels.iv import IV2SLS, IVGMM, IVLIML

    regressand = regressand_column(spec.regressand, outlier_threshold)
    if regressand not in sample.columns:
        raise KeyError(
            f"{regressand!r} is not in this panel: the outlier-threshold variant "
            f"{outlier_threshold} is not available for this source (ADR-0008)"
        )
    exog = list(spec.exog)
    endog = list(spec.endog)
    instruments = list(spec.instruments) if spec.is_iv else []
    needed = [regressand, *exog, *endog, *instruments]
    absent = [name for name in needed if name not in sample.columns]
    if absent:
        raise PublicPanelIncomplete(
            f"this column of the published specification needs {absent}, which this panel does "
            "not carry. A near-equivalent column is not a substitute: see "
            "`docs/declared-differences.md`. Run `--source private` for the benchmark, or add "
            "the variables to the panel."
        )
    data = sample.dropna(subset=needed).copy()
    data = data.sort_values(["od", "ym"]).reset_index(drop=True)
    data["_route_index"] = pd.factorize(data["od"])[0]

    included = exog if spec.is_iv else exog + endog
    x_included, included_names, dropped = design(data, included, with_seasonality=with_seasonality)
    y = data[regressand].to_numpy(np.float64)
    panel = (data["_route_index"].to_numpy(), data["_time_index"].to_numpy()) if panel_hac else None

    dep = pd.Series(y, name=regressand)
    exog_frame = pd.DataFrame(x_included, columns=included_names)
    kernel = {"cov_type": "kernel", "kernel": "bartlett", "bandwidth": bandwidth}

    if spec.is_iv:
        endog_frame = pd.DataFrame(data[endog].to_numpy(np.float64), columns=endog)
        instr_frame = pd.DataFrame(data[instruments].to_numpy(np.float64), columns=instruments)
        if spec.estimator == "gmm2s":
            model = IVGMM(
                dep,
                exog_frame,
                endog_frame,
                instr_frame,
                weight_type="kernel",
                kernel="bartlett",
                bandwidth=bandwidth,
            )
            result = model.fit(iter_limit=2, debiased=debiased, **kernel)
            j_stat, j_p, j_df = (
                float(result.j_stat.stat),
                float(result.j_stat.pval),
                int(result.j_stat.df),
            )
        else:
            result = IVLIML(dep, exog_frame, endog_frame, instr_frame).fit(
                debiased=debiased, **kernel
            )
            all_instruments = np.hstack([x_included, instr_frame.to_numpy()])
            j_stat, j_p, j_df = hansen_j(
                result.resids.to_numpy(),
                all_instruments,
                bandwidth=bandwidth,
                panel=panel,
                n_params_overid=len(instruments) - len(endog),
            )
    else:
        result = IV2SLS(dep, exog_frame, None, None).fit(debiased=debiased, **kernel)
        j_stat = j_p = float("nan")
        j_df = 0

    params, errors = result.params, result.std_errors
    coefficients = {
        name: {"b": float(params[name]), "se": float(errors[name])}
        for name in COEF_ORDER
        if name in params.index
    }

    residuals = result.resids.to_numpy()
    n_obs = len(data)
    n_params = x_included.shape[1] + (len(endog) if spec.is_iv else 0)
    rss = float(residuals @ residuals)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - rss / tss
    stats: dict[str, Any] = {
        "n_obs": n_obs,
        "n_params": int(n_params),
        "n_routes": int(data["od"].nunique()),
        "adj_r2": float(1 - (1 - r2) * (n_obs - 1) / (n_obs - n_params)),
        "rmse": float(np.sqrt(rss / (n_obs - n_params))),
        "rmse_large_sample": float(np.sqrt(rss / n_obs)),
        "j_stat": j_stat,
        "j_p": j_p,
        "j_df": j_df,
        "f_stat": None,  # declared difference: see docs/declared-differences.md
    }

    if spec.is_iv:
        endog_partialled = kpmod.partial_out(data[endog].to_numpy(np.float64), x_included)
        instr_partialled = kpmod.partial_out(data[instruments].to_numpy(np.float64), x_included)
        rk = kpmod.rk_statistics(
            endog_partialled, instr_partialled, bandwidth=bandwidth, panel=panel
        )
        cd = kpmod.cragg_donald(endog_partialled, instr_partialled)
        stats.update(
            {
                "kp_lm": rk.lm,
                "kp_p": rk.lm_pvalue,
                "kp_df": rk.df,
                "kp_wald": rk.wald,
                "weak_kp_f": rk.wald_f,
                "weak_cd_f": cd["wald_f"],
                "cd_lambda_min": cd["lambda_min"],
            }
        )
    return ColumnResult(
        column=spec.column,
        regressand=regressand,
        estimator=spec.estimator,
        coefficients=coefficients,
        stats=stats,
        dropped_collinear=dropped,
    )


def run_table(
    specs: list[ColumnSpec],
    *,
    source: Source | str = Source.PRIVATE,
    filter_regressand: str = "fsc_oddsarr",
    sample: pd.DataFrame | None = None,
    **fit_kwargs: Any,
) -> dict[str, Any]:
    """Estimate every column of one table on one shared sample."""
    if sample is None:
        sample = build_sample(source, filter_regressand=filter_regressand)
    columns = {str(spec.column): fit(sample, spec, **fit_kwargs).as_dict() for spec in specs}
    return {"sample": dict(sample.attrs.get("filters", {})), "columns": columns}
