import numpy as np


def PowerLaw(
    k,
    k_s=0.05,
    logA=3.044,
    n_s=0.965,
):
    A_s = np.exp(logA) * 1e-10
    PL = A_s * (k / k_s) ** (n_s - 1.0)
    return PL


def OneSpectrum(
    k,
    alpha=0.08,
    log10beta=6,
    k_0=0.138,
    w=290,
    k_s=0.05,
    logA=3.044,
    n_s=0.965,
):
    beta = 10**log10beta
    num = alpha * np.sin(w * (k - k_0))
    den = 1 + beta * (k - k_0) ** 4
    return PowerLaw(k) * (1 + num / den)


def DampedLog(k, logA=3.044, n_s=0.965, Alog=0.1, log10w=1, beta=4, mu=0.03, k_0=0.05):
    env = np.exp(-(beta**2) * (k - mu) ** 2 / 2 / k_0**2)
    wlog = 10**log10w
    phi = -wlog * np.log(mu / k_0)
    return (
        np.exp(logA)
        * 10 ** (-10)
        * (k / k_0) ** (n_s - 1.0)
        * (1 + Alog * np.cos(wlog * np.log(k / k_0) + phi) * env)
    )
