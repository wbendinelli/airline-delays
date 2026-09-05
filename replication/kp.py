"""Kleibergen-Paap rk statistics, Cragg-Donald Wald, and the HAC machinery they share.

No Python package implements the Kleibergen and Paap (2006, *Journal of
Econometrics* 133, 97-126) ``rk`` statistic: ``linearmodels`` 7.0 reports
first-stage partial F and partial R-squared, Hansen's J, Wu-Hausman and Sargan
but nothing named *kleibergen*, *ranktest* or *cragg*; ``pyfixest`` has the
Olea-Pflueger effective F for a single endogenous regressor; ``ivmodels``
exposes a Cragg-Donald rank test and the Kleibergen (2002) LM test *for beta*,
which is a test of a parameter, not of a rank. Stata's ``ranktest`` and R's
``ivreg2r`` are the reference implementations. This module is written from the
paper and validated two ways: an exact algebraic collapse under i.i.d. errors
(``tests/test_replication_kp.py``) and a regression test against the published
values of Bendinelli, Bettini and Oliveira (2016) (same file).

The construction, with ``Y`` the endogenous regressors and ``Z`` the excluded
instruments, both after partialling out the included exogenous regressors::

    Pi   = (Z'Z)^-1 Z'Y                                  # L x k2 reduced form
    Th   = (Z'Z/N)^(1/2) . Pi . Svv^(-1/2)               # canonical-correlation metric
    W_Th = (Svv^(-1/2) (x) (Z'Z/N)^(1/2)) W_Pi (.)'      # (x) = Kronecker
    Th   = U S V'                                        # SVD
    A_p  = U[:, q:] ,  B_p = V[:, q:]
    Lam  = A_p' Th B_p
    rk   = N vec(Lam)' [ (B_p (x) A_p)' W_Th (B_p (x) A_p) ]^-1 vec(Lam)

which is chi-squared with ``(L - q)(k2 - q)`` degrees of freedom under
``H0: rank(Pi) = q``. ``W_Pi`` is the covariance of ``sqrt(N) vec(Pi)``, HAC by
default and i.i.d. on request.

**The normalisation matters.** The SVD partition is not invariant to the metric:
feeding the raw ``Pi`` instead of ``Th`` changes the number outright. What pins
it down is a pair of exact collapses under i.i.d. errors, at the
underidentification null ``q = k2 - 1``: the Wald form becomes the
Cragg-Donald Wald statistic ``N lambda / (1 - lambda)`` and the LM form becomes
Anderson's canonical-correlation LM ``N lambda``, with ``lambda`` the smallest
squared canonical correlation. Both are asserted to machine precision in
``tests/test_replication_kp.py`` against an independent implementation
(:func:`cragg_donald`, which goes through QR and an SVD of the projections and
shares no code with :func:`kp_rk`).

Two versions of the same statistic, exactly as ``ivreg2`` reports them:

``lm``
    Covariance built from reduced-form residuals *restricted to rank q* (the
    SVD truncated at ``q``). This is the "KP statistic" row of the published
    tables, the underidentification test.
``wald``
    Covariance built from unrestricted residuals. Divided by ``L`` it is the
    "Weak KP statistic" row.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from scipy import stats as _stats

Errors = Literal["hac", "iid"]

__all__ = [
    "KPResult",
    "bartlett_weights",
    "cragg_donald",
    "hac_moment_cov",
    "kp_rk",
    "partial_out",
    "rk_statistics",
]


# --------------------------------------------------------------------- helpers
def partial_out(target: np.ndarray, controls: np.ndarray) -> np.ndarray:
    """Residuals of `target` on `controls` (identity when there are no controls)."""
    if controls.shape[1] == 0:
        return target
    return target - controls @ np.linalg.lstsq(controls, target, rcond=None)[0]


def bartlett_weights(bandwidth: int) -> np.ndarray:
    """Bartlett kernel weights ``1 - j/(bandwidth + 1)`` for lags ``j = 1..bandwidth``.

    ``linearmodels`` uses this convention, so ``bandwidth=4`` here is Stata's
    ``ivreg2 ..., bw(5)``, whose weights are ``1 - j/5`` for ``j = 0..4``.
    """
    j = np.arange(1, bandwidth + 1, dtype=float)
    return 1.0 - j / (bandwidth + 1)


def hac_moment_cov(
    moments: np.ndarray,
    bandwidth: int,
    route_index: np.ndarray | None = None,
    time_index: np.ndarray | None = None,
) -> np.ndarray:
    """Newey-West/Bartlett HAC covariance ``S = G0 + sum_j w_j (Gj + Gj')``.

    With `route_index` and `time_index` unset the lag is measured in **row
    order**, which is what ``linearmodels`` does; autocovariances then cross
    panel-unit boundaries. With both given the lag is measured in **periods
    within a unit**, so only pairs from the same route separated by exactly `j`
    months enter and gaps in the unbalanced panel are respected -- what Stata's
    ``tsset`` would do. Both are offered because the difference is a measured
    quantity, not a matter of taste (see ``docs/notes/replication.md``).
    """
    n = moments.shape[0]
    cov = moments.T @ moments / n
    weights = bartlett_weights(bandwidth)
    if route_index is None or time_index is None:
        for lag, weight in enumerate(weights, start=1):
            cross = moments[lag:].T @ moments[:-lag] / n
            cov += weight * (cross + cross.T)
        return cov
    n_routes = int(route_index.max()) + 1
    n_periods = int(time_index.max()) + 1
    position = -np.ones((n_routes, n_periods), dtype=np.int64)
    position[route_index, time_index] = np.arange(n)
    for lag, weight in enumerate(weights, start=1):
        later, earlier = position[:, lag:], position[:, :-lag]
        both = (later >= 0) & (earlier >= 0)
        cross = moments[later[both]].T @ moments[earlier[both]] / n
        cov += weight * (cross + cross.T)
    return cov


def _sqrtm_psd(matrix: np.ndarray, *, inverse: bool = False) -> np.ndarray:
    """Symmetric square root (or inverse square root) of a PSD matrix."""
    values, vectors = np.linalg.eigh((matrix + matrix.T) / 2)
    values = np.clip(values, 1e-14, None)
    values = 1 / np.sqrt(values) if inverse else np.sqrt(values)
    return (vectors * values) @ vectors.T


# --------------------------------------------------------------------- results
@dataclass(frozen=True)
class KPResult:
    """The rk statistic at one null rank `q`, in both of its published forms."""

    q: int
    df: int
    lm: float
    wald: float
    n_instruments: int
    canonical_singular_values: tuple[float, ...] = field(default=())

    @property
    def lm_pvalue(self) -> float:
        return float(_stats.chi2.sf(self.lm, self.df)) if self.df > 0 else float("nan")

    @property
    def wald_pvalue(self) -> float:
        return float(_stats.chi2.sf(self.wald, self.df)) if self.df > 0 else float("nan")

    @property
    def wald_f(self) -> float:
        """The "Weak KP statistic" of the published tables: rk Wald divided by L."""
        return self.wald / self.n_instruments

    def as_dict(self) -> dict[str, float | int | list[float]]:
        return {
            "q": self.q,
            "df": self.df,
            "lm": self.lm,
            "lm_pvalue": self.lm_pvalue,
            "wald": self.wald,
            "wald_pvalue": self.wald_pvalue,
            "wald_f": self.wald_f,
            "n_instruments": self.n_instruments,
            "canonical_singular_values": list(self.canonical_singular_values),
        }


# ------------------------------------------------------------------ statistics
def kp_rk(
    endog: np.ndarray,
    instruments: np.ndarray,
    included_exog: np.ndarray | None = None,
    *,
    bandwidth: int = 4,
    panel: tuple[np.ndarray, np.ndarray] | None = None,
    errors: Errors = "hac",
    ranks: list[int] | None = None,
) -> dict[int, KPResult]:
    """Kleibergen-Paap rk LM and Wald for every null rank `q`.

    Parameters
    ----------
    endog, instruments, included_exog
        ``N x k2``, ``N x L`` and ``N x K1`` design blocks. `included_exog` is
        partialled out of the other two first; pass ``None`` for none.
    bandwidth
        Bartlett bandwidth in the ``linearmodels`` convention (4 == Stata's
        ``bw(5)``). Ignored when ``errors="iid"``.
    panel
        ``(route_index, time_index)`` to measure HAC lags within a route
        instead of by row order.
    errors
        ``"hac"`` for the Bartlett covariance of the moments; ``"iid"`` for the
        classical ``Svv (x) (Z'Z/N)^-1``, under which the Wald form collapses
        to the Cragg-Donald Wald statistic -- the identity the fixture test
        asserts.
    ranks
        Null ranks to test; defaults to ``0 .. k2-1``. The published "KP
        statistic" is the underidentification test at ``q = k2 - 1``.
    """
    controls = np.zeros((endog.shape[0], 0)) if included_exog is None else included_exog
    y_resid = partial_out(np.asarray(endog, dtype=float), controls)
    z_resid = partial_out(np.asarray(instruments, dtype=float), controls)
    n, n_ins = z_resid.shape
    k2 = y_resid.shape[1]
    if k2 == 0 or n_ins == 0:
        raise ValueError("kp_rk needs at least one endogenous regressor and one instrument")

    zz = z_resid.T @ z_resid / n
    pi = np.linalg.solve(zz, z_resid.T @ y_resid / n)
    resid_unrestricted = y_resid - z_resid @ pi
    svv = resid_unrestricted.T @ resid_unrestricted / n

    zz_sqrt = _sqrtm_psd(zz)
    svv_inv_sqrt = _sqrtm_psd(svv, inverse=True)
    theta = zz_sqrt @ pi @ svv_inv_sqrt
    to_theta = np.kron(svv_inv_sqrt, zz_sqrt)
    from_pi = np.kron(np.eye(k2), np.linalg.pinv(zz))
    left, singular, right_t = np.linalg.svd(theta, full_matrices=True)

    def statistic(q: int, *, restricted: bool) -> float:
        if restricted:
            if q > 0:
                theta_r = left[:, :q] @ np.diag(singular[:q]) @ right_t[:q, :]
            else:
                theta_r = np.zeros_like(theta)
            pi_r = np.linalg.solve(zz_sqrt, theta_r) @ np.linalg.pinv(svv_inv_sqrt)
            resid = y_resid - z_resid @ pi_r
        else:
            resid = resid_unrestricted
        if errors == "iid":
            omega = np.kron(resid.T @ resid / n, zz)
        else:
            # g_i = vec(z_i v_i') = (v_i (x) z_i), stacked column by column.
            moments = np.einsum("ij,ik->ikj", resid, z_resid).reshape(n, n_ins * k2, order="F")
            omega = hac_moment_cov(moments, bandwidth, *(panel if panel else (None, None)))
        weight = to_theta @ (from_pi @ omega @ from_pi.T) @ to_theta.T
        a_perp, b_perp = left[:, q:], right_t[q:, :].T
        lam = (a_perp.T @ theta @ b_perp).reshape(-1, order="F")
        kron = np.kron(b_perp, a_perp)
        return float(n * lam @ np.linalg.pinv(kron.T @ weight @ kron) @ lam)

    wanted = list(range(k2)) if ranks is None else list(ranks)
    return {
        q: KPResult(
            q=q,
            df=(n_ins - q) * (k2 - q),
            lm=statistic(q, restricted=True),
            wald=statistic(q, restricted=False),
            n_instruments=n_ins,
            canonical_singular_values=tuple(float(value) for value in singular),
        )
        for q in wanted
    }


def rk_statistics(
    endog: np.ndarray,
    instruments: np.ndarray,
    included_exog: np.ndarray | None = None,
    **kwargs: object,
) -> KPResult:
    """The published pair: rk LM and rk Wald F at ``q = k2 - 1`` (underidentification)."""
    k2 = np.asarray(endog).shape[1]
    return kp_rk(endog, instruments, included_exog, ranks=[k2 - 1], **kwargs)[k2 - 1]  # type: ignore[arg-type]


def cragg_donald(
    endog: np.ndarray,
    instruments: np.ndarray,
    included_exog: np.ndarray | None = None,
) -> dict[str, float]:
    """Cragg-Donald Wald statistic and the Anderson canonical-correlation LM.

    ``lambda`` is the smallest squared canonical correlation between the
    endogenous regressors and the excluded instruments, both partialled. The
    Wald statistic is ``N lambda / (1 - lambda)``; the published "Weak CD
    statistic" divides it by the number of excluded instruments. ``anderson_lm``
    is the ``N lambda`` form. Under i.i.d. errors the rk Wald at
    ``q = k2 - 1`` equals ``wald`` and the rk LM equals ``anderson_lm``, which is
    how :func:`kp_rk` is validated.
    """
    controls = np.zeros((np.asarray(endog).shape[0], 0)) if included_exog is None else included_exog
    y_resid = partial_out(np.asarray(endog, dtype=float), controls)
    z_resid = partial_out(np.asarray(instruments, dtype=float), controls)
    n, n_ins = z_resid.shape
    q_y = np.linalg.qr(y_resid)[0]
    q_z = np.linalg.qr(z_resid)[0]
    singular = np.linalg.svd(q_y.T @ q_z, compute_uv=False)
    lam = float(np.clip(singular.min(), 0.0, 1.0) ** 2)
    wald = n * lam / (1 - lam)
    return {
        "lambda_min": lam,
        "wald": wald,
        "wald_f": wald / n_ins,
        "anderson_lm": n * lam,
        "n_instruments": float(n_ins),
    }
