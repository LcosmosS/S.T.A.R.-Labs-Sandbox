"""Seeded Metropolis-Hastings cosmology fitter."""

from __future__ import annotations

import numpy as np

from src.physics.symbolic_cosmology import SymbolicCosmology


class MCMCCosmologyFitter:
    def __init__(
        self,
        H_expr,
        param_names,
        priors,
        proposal_widths,
        *,
        seed: int,
    ):
        self.H_expr = H_expr
        self.param_names = list(param_names)
        self.priors = priors
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)

        normalized_widths = {}
        for name in self.param_names:
            if name not in proposal_widths:
                raise KeyError(f"missing proposal width for {name}")
            width = float(proposal_widths[name])
            if not np.isfinite(width) or width <= 0:
                raise ValueError(
                    f"proposal width must be finite and positive for {name}"
                )
            normalized_widths[name] = width
        self.proposal_widths = normalized_widths

    def _log_prior(self, theta):
        lp = 0.0
        for val, name in zip(theta, self.param_names):
            mu, sigma = self.priors[name]
            if not np.isfinite(mu) or not np.isfinite(sigma) or sigma <= 0:
                raise ValueError(
                    f"prior parameters must be finite with positive sigma for {name}"
                )
            lp += -0.5 * ((val - mu) / sigma) ** 2
        return float(lp)

    def _log_likelihood(self, theta, z, mu_obs, sigma_mu):
        params = dict(zip(self.param_names, theta))
        model = SymbolicCosmology(self.H_expr, params)
        try:
            mu_model = np.asarray(
                [model.distance_modulus(zi) for zi in z],
                dtype=float,
            )
        except FloatingPointError:
            return -np.inf
        if not np.all(np.isfinite(mu_model)):
            return -np.inf
        chi2 = np.sum(((mu_obs - mu_model) / sigma_mu) ** 2)
        return float(-0.5 * chi2) if np.isfinite(chi2) else -np.inf

    def _log_posterior(self, theta, z, mu_obs, sigma_mu):
        value = self._log_prior(theta) + self._log_likelihood(
            theta, z, mu_obs, sigma_mu
        )
        return float(value) if np.isfinite(value) else -np.inf

    def run(self, z, mu_obs, sigma_mu, theta0, nsteps=5000):
        z = np.asarray(z, dtype=float)
        mu_obs = np.asarray(mu_obs, dtype=float)
        sigma_mu = np.asarray(sigma_mu, dtype=float)
        theta0 = np.asarray(theta0, dtype=float)

        if not (z.shape == mu_obs.shape == sigma_mu.shape):
            raise ValueError("z, mu_obs, and sigma_mu must have equal shapes")
        if z.size == 0:
            raise ValueError("at least one observation is required")
        if not np.all(np.isfinite(z)) or not np.all(np.isfinite(mu_obs)):
            raise ValueError("z and mu_obs must contain only finite values")
        if np.any(sigma_mu <= 0) or not np.all(np.isfinite(sigma_mu)):
            raise ValueError("sigma_mu must be finite and positive")
        if theta0.size != len(self.param_names):
            raise ValueError("theta0 length must match param_names")
        if not np.all(np.isfinite(theta0)):
            raise ValueError("theta0 must contain only finite values")
        if int(nsteps) < 2:
            raise ValueError("nsteps must be at least 2")

        chain = np.zeros((int(nsteps), len(theta0)), dtype=float)
        chain[0] = theta0
        logp = self._log_posterior(theta0, z, mu_obs, sigma_mu)
        if not np.isfinite(logp):
            raise ValueError("initial parameter vector has a non-finite posterior")

        for i in range(1, int(nsteps)):
            proposal = chain[i - 1].copy()
            for j, name in enumerate(self.param_names):
                proposal[j] += self.rng.normal(
                    0.0, float(self.proposal_widths[name])
                )

            logp_new = self._log_posterior(proposal, z, mu_obs, sigma_mu)
            accept = False
            if np.isfinite(logp_new):
                log_alpha = min(0.0, logp_new - logp)
                accept = np.log(self.rng.random()) < log_alpha

            if accept:
                chain[i] = proposal
                logp = logp_new
            else:
                chain[i] = chain[i - 1]

        return chain
