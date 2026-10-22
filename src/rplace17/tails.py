"""
rplace17.tails: fitting and comparing heavy-tailed distributions at the scale of the r/place log (millions of values).

The method is Clauset, Shalizi and Newman (2009): fit a power law above a cutoff xmin by maximum likelihood, choose
xmin by minimising the Kolmogorov-Smirnov distance, and compare against other distributions above the same xmin by
likelihood ratio (Vuong's test). What changes is only the implementation, so that it scales:

  - the data are sorted once; with a running sum of log x, the power-law MLE at every candidate xmin is a formula;
  - candidate xmins are a grid of quantiles, not every distinct value;
  - the KS distance is evaluated at a grid of points of the tail (ks_points), not at every point: the error is at most
    about 1/ks_points in the CDF, far below the distances seen here;
  - the alternatives are fitted on the tail by numerical maximum likelihood, vectorised over the tail.

All fits are continuous. Values must be positive.

    f = fit(x)                       # power law: xmin, alpha, n_tail, D, the scan over xmin
    compare(x, f)                    # the alternatives above f.xmin, with likelihood ratios
    bootstrap_accounts(x, acc, ...)  # confidence intervals for alpha and xmin, resampling accounts
"""
from dataclasses import dataclass

import numpy as np
import polars as pl
from scipy import integrate, optimize, stats


@dataclass
class PowerLawFit:
    xmin: float
    alpha: float
    n_tail: int
    n: int
    D: float
    at_boundary: bool          # True if the best xmin is the largest candidate: no stable tail was found
    scan: pl.DataFrame         # every candidate: xmin, alpha, n_tail, D
    decades: float             # log10(max / xmin): how much range the tail spans


def _ks(tail_sorted, cdf, ks_points):
    """KS distance between the empirical CDF of a sorted tail and a model CDF, on a grid of tail points."""
    n = len(tail_sorted)
    idx = np.unique(np.linspace(0, n - 1, min(n, ks_points)).astype(np.int64))
    m = cdf(tail_sorted[idx])
    return float(max(np.max(np.abs(m - idx / n)), np.max(np.abs(m - (idx + 1) / n))))


def fit(x, n_candidates=200, q_max=0.99, min_tail=1000, ks_points=2000, weights=None):
    """Power-law fit above the KS-optimal xmin. weights: optional non-negative weight per value (for bootstraps)."""
    x = np.asarray(x, float)
    order = np.argsort(x, kind="stable")
    x = x[order]
    w = np.ones_like(x) if weights is None else np.asarray(weights, float)[order]
    lx = np.log(x)
    W = np.cumsum(w[::-1])[::-1]                       # W[i]  = total weight at or above x[i]
    S = np.cumsum((w * lx)[::-1])[::-1]               # S[i]  = sum of w log x at or above x[i]
    qs = np.linspace(0.0, q_max, n_candidates)
    cand = np.unique(np.searchsorted(x, np.quantile(x, qs)))
    cand = cand[(len(x) - cand) >= min_tail]
    rows = []
    for i in cand:
        n_t = W[i]
        if n_t <= 0:
            continue
        xm = x[i]
        alpha = 1 + n_t / (S[i] - n_t * np.log(xm))
        tail = x[i:]
        if weights is None:
            D = _ks(tail, lambda v: 1 - (v / xm) ** (1 - alpha), ks_points)
        else:                                          # weighted empirical CDF on the grid
            cw = np.cumsum(w[i:]) / n_t
            idx = np.unique(np.linspace(0, len(tail) - 1, min(len(tail), ks_points)).astype(np.int64))
            m = 1 - (tail[idx] / xm) ** (1 - alpha)
            D = float(np.max(np.abs(m - cw[idx])))
        rows.append((xm, alpha, int(round(n_t)), D))
    scan = pl.DataFrame(rows, schema=["xmin", "alpha", "n_tail", "D"], orient="row")
    best = scan.row(int(np.argmin(scan["D"].to_numpy())), named=True)
    return PowerLawFit(xmin=best["xmin"], alpha=best["alpha"], n_tail=best["n_tail"], n=int(round(w.sum())), D=best["D"],
                       at_boundary=best["xmin"] == scan["xmin"].max(), scan=scan,
                       decades=float(np.log10(x[-1] / best["xmin"])))


# ---------------------------------------------------------------- the alternatives, all truncated at xmin
def _loglik_power_law(t, xm, alpha):
    return np.log((alpha - 1) / xm) - alpha * np.log(t / xm)


def _fit_exponential(t, xm):
    lam = 1 / (t.mean() - xm)
    return {"lambda": lam}, np.log(lam) - lam * (t - xm)


def _fit_lognormal(t, xm):
    lt = np.log(t)
    def ll(p):
        mu, s = p[0], np.exp(p[1])
        return -np.log(t * s * np.sqrt(2 * np.pi)) - (lt - mu) ** 2 / (2 * s * s) - stats.norm.logsf((np.log(xm) - mu) / s)
    res = optimize.minimize(lambda p: -ll(p).sum(), [lt.mean(), np.log(lt.std() + 1e-9)], method="Nelder-Mead",
                            options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": 2000})
    return {"mu": res.x[0], "sigma": float(np.exp(res.x[1]))}, ll(res.x)


def _fit_stretched_exponential(t, xm):
    lt = np.log(t)
    def ll(p):
        beta, lam = np.exp(np.clip(p[0], -8, 2)), np.exp(np.clip(p[1], -40, 20))   # keep the optimiser in range
        with np.errstate(over="ignore", invalid="ignore"):
            v = np.log(beta) + beta * np.log(lam) + (beta - 1) * lt - lam ** beta * (t ** beta - xm ** beta)
        return np.where(np.isfinite(v), v, -1e300)
    res = optimize.minimize(lambda p: -ll(p).sum(), [np.log(0.5), -np.log(t.mean())], method="Nelder-Mead",
                            options={"xatol": 1e-7, "fatol": 1e-6, "maxiter": 4000})
    return {"beta": float(np.exp(np.clip(res.x[0], -8, 2))), "lambda": float(np.exp(np.clip(res.x[1], -40, 20)))}, ll(res.x)


def _fit_truncated_power_law(t, xm, alpha0):
    lt = np.log(t)
    def logZ(alpha, lam):        # log of the integral of x^-alpha e^(-lam x) from xm to infinity, in u = log x
        f = lambda u: np.exp(-(alpha - 1) * (u - np.log(xm)) - lam * (np.exp(u) - xm))
        val, _ = integrate.quad(f, np.log(xm), np.log(xm) + 60, limit=200)
        return np.log(val) + (1 - alpha) * np.log(xm) - lam * xm
    def nll(p):
        alpha, lam = p[0], np.exp(p[1])
        return -(-alpha * lt - lam * t - logZ(alpha, lam)).sum()
    res = optimize.minimize(nll, [alpha0, np.log(1 / t.mean())], method="Nelder-Mead",
                            options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": 2000})
    alpha, lam = res.x[0], float(np.exp(res.x[1]))
    return {"alpha": alpha, "lambda": lam}, -alpha * lt - lam * t - logZ(alpha, lam)


def compare(x, f, return_params=False):
    """Likelihood ratios of the power law against each alternative, above f.xmin. R > 0 favours the power law.
    Non-nested pairs: Vuong's normalised ratio and two-sided p. The truncated power law contains the power law, so for it
    p is the likelihood-ratio test (2 x the log-likelihood difference against chi-squared with 1 df)."""
    x = np.asarray(x, float)
    t = x[x >= f.xmin]
    lp = _loglik_power_law(t, f.xmin, f.alpha)
    out = [{"model": "power law", "params": f"alpha {f.alpha:.3f}", "logL": float(lp.sum()), "R": 0.0,
            "normalised R": float("nan"), "p": float("nan")}]
    fitted = {"power law": {"alpha": f.alpha}}
    for name, fitter in (("exponential", _fit_exponential), ("lognormal", _fit_lognormal),
                         ("stretched exponential", _fit_stretched_exponential),
                         ("truncated power law", lambda tt, xm: _fit_truncated_power_law(tt, xm, f.alpha))):
        params, lq = fitter(t, f.xmin)
        fitted[name] = params
        d = lp - lq
        R = float(d.sum())
        if name == "truncated power law":
            z, p = float("nan"), float(stats.chi2.sf(max(-2 * R, 0), 1))
        else:
            z = R / (d.std() * np.sqrt(len(d)))
            p = float(2 * stats.norm.sf(abs(z)))
        out.append({"model": name, "params": ", ".join(f"{k} {v:.4g}" for k, v in params.items()), "logL": float(lq.sum()),
                    "R": R, "normalised R": z, "p": p})
    return (pl.DataFrame(out), fitted) if return_params else pl.DataFrame(out)


def model_ccdf(name, params, xmin, x):
    """P(X >= x | X >= xmin) under a fitted model, for overlaying on the data's CCDF (truncated power law omitted)."""
    x = np.asarray(x, float)
    if name == "power law":
        return (x / xmin) ** (1 - params["alpha"])
    if name == "exponential":
        return np.exp(-params["lambda"] * (x - xmin))
    if name == "lognormal":
        mu, s = params["mu"], params["sigma"]
        return np.exp(stats.norm.logsf((np.log(x) - mu) / s) - stats.norm.logsf((np.log(xmin) - mu) / s))
    if name == "stretched exponential":
        b, lam = params["beta"], params["lambda"]
        return np.exp(-(lam ** b) * (x ** b - xmin ** b))
    raise ValueError(name)


def bootstrap_accounts(x, accounts, B=200, seed=0, **kw):
    """Confidence intervals for alpha and xmin, resampling accounts (values from one account are not independent).
    Each replicate weights every account by a multinomial count, i.e. a resample of accounts with replacement."""
    rng = np.random.default_rng(seed)
    acc = np.asarray(accounts)
    uniq, inv = np.unique(acc, return_inverse=True)
    alphas, xmins = [], []
    for _ in range(B):
        w_acc = rng.multinomial(len(uniq), np.full(len(uniq), 1 / len(uniq)))
        f = fit(x, weights=w_acc[inv], **kw)
        alphas.append(f.alpha); xmins.append(f.xmin)
    return {"alpha_ci": tuple(np.quantile(alphas, [0.025, 0.975])), "xmin_ci": tuple(np.quantile(xmins, [0.025, 0.975])),
            "alphas": np.array(alphas), "xmins": np.array(xmins)}


def exponential_null(x, accounts, seed=0, cap=None):
    """Per-account null: each account's values replaced by exponential draws with that account's own mean, the same
    number of them. Pooled, this shows how heavy a tail differences in rate between accounts produce on their own.
    cap: if given, draws are from the exponential truncated at cap (as the data are, by the length of the event),
    with the rate solved per account so the truncated mean still equals the account's own mean."""
    rng = np.random.default_rng(seed)
    df = pl.DataFrame({"a": np.asarray(accounts), "x": np.asarray(x, float)})
    means = df.group_by("a").agg(pl.col("x").mean().alias("m"))
    m = df.join(means, on="a", how="left")["m"].to_numpy()
    if cap is None:
        return rng.exponential(m)
    # mean of Exp(scale s) truncated at cap: s - cap / (exp(cap / s) - 1); solve for s with a few Newton-free bisection steps
    um, inv = np.unique(m, return_inverse=True)
    lo, hi = np.full(len(um), 1e-6), np.full(len(um), 1e9)
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        with np.errstate(over="ignore"):
            tm = mid - cap / np.expm1(np.minimum(cap / mid, 700))
        too_big = tm > um
        hi = np.where(too_big, mid, hi); lo = np.where(too_big, lo, mid)
    scale = np.sqrt(lo * hi)[inv]
    u = rng.random(len(m))
    return -scale * np.log1p(-u * (-np.expm1(-cap / scale)))          # inverse CDF of the truncated exponential


def ccdf(x, max_points=4000):
    """Points of the complementary CDF, P(X >= x), thinned to at most max_points for plotting."""
    xs = np.sort(np.asarray(x, float))
    p = 1 - np.arange(len(xs)) / len(xs)
    idx = np.unique(np.geomspace(1, len(xs), max_points).astype(np.int64) - 1)
    return xs[idx], p[idx]
