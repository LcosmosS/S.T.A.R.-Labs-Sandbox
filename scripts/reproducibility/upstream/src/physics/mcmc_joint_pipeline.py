"""Deterministic Metropolis-Hastings pipeline for joint cosmology inference."""

from __future__ import annotations

import numpy as np

from src.physics.symbolic_cosmology import SymbolicCosmology


class JointMCMCPipeline:
    def __init__(
        self,
        H_expr,
        param_names,
        priors,
        proposal_widths,
        joint_likelihood,
        *,
        seed: int,
        fixed_params=None,
    ):
        self.H_expr = H_expr
        self.param_names = list(param_names)
        self.priors = priors
        self.proposal_widths = proposal_widths
        self.joint_likelihood = joint_likelihood
        self.seed = int(seed)
        self.fixed_params = dict(fixed_params or {})
        self.rng = np.random.default_rng(self.seed)

        missing_priors = [name for name in self.param_names if name not in self.priors]
        missing_widths = [
            name for name in self.param_names if name not in self.proposal_widths
        ]
        if missing_priors:
            raise KeyError(f"missing priors for parameters: {missing_priors}")
        if missing_widths:
            raise KeyError(f"missing proposal widths for parameters: {missing_widths}")

    def _log_prior(self, theta):
        lp = 0.0
        for value, name in zip(theta, self.param_names):
            mu, sigma = self.priors[name]
            if sigma <= 0:
                raise ValueError(f"prior sigma must be positive for {name}")
            if name in {"Ωm", "ΩΛ"} and value < 0:
                return -np.inf
            if name == "H0" and value <= 0:
                return -np.inf
            lp += -0.5 * ((value - mu) / sigma) ** 2
        return float(lp)

    def _model_from_theta(self, theta):
        params = dict(zip(self.param_names, np.asarray(theta, dtype=float)))
        overlap = set(params) & set(self.fixed_params)
        if overlap:
            raise ValueError(
                f"parameters cannot be both sampled and fixed: {sorted(overlap)}"
            )
        params.update(self.fixed_params)
        return SymbolicCosmology(self.H_expr, params)

    def _log_posterior(self, theta):
        lp = self._log_prior(theta)
        if not np.isfinite(lp):
            return -np.inf
        try:
            ll = float(self.joint_likelihood(self._model_from_theta(theta)))
        except (FloatingPointError, ValueError, KeyError, TypeError):
            return -np.inf
        if not np.isfinite(ll):
            return -np.inf
        return float(lp + ll)

    def run(self, theta0, nsteps=5000):
        theta0 = np.asarray(theta0, dtype=float).flatten()
        if theta0.size != len(self.param_names):
            raise ValueError("theta0 length must match param_names")
        if nsteps < 2:
            raise ValueError("nsteps must be at least 2")

        chain = np.zeros((int(nsteps), theta0.size), dtype=float)
        chain[0] = theta0
        logp = self._log_posterior(theta0)
        if not np.isfinite(logp):
            raise ValueError(
                "initial parameter vector has a non-finite posterior; "
                "controlled inference will not substitute a finite penalty"
            )

        for i in range(1, int(nsteps)):
            proposal = chain[i - 1].copy()
            for j, name in enumerate(self.param_names):
                proposal[j] += self.rng.normal(0.0, self.proposal_widths[name])

            logp_new = self._log_posterior(proposal)
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
