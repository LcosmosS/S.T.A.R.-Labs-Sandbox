"""Fail-closed predictor/holdout guards for prospectively audited SFR workflows."""
from __future__ import annotations
from collections.abc import Mapping

class LeakageGateError(ValueError):
    pass

TARGET_SFR = "log_sfr_ha"
DIRECT_TARGET_ALIASES = frozenset({
    "log_sfr_ha", "log_sfr_ha_raw", "sfr_ha", "sfr_ha_raw",
    "log_sfr", "sfr", "sfr_halpha", "log_sfr_halpha",
    "ha_luminosity", "l_ha", "halpha_flux", "ha_flux", "flux_ha",
})

def validate_feature_names(names, *, target="log_SFR_Ha", target_descendants=()):
    """Reject known direct target proxies and explicit target-derived lineage.

    Feature importance or a high held-out score never proves absence of leakage.
    """
    if target.casefold()!=TARGET_SFR:
        raise LeakageGateError("SFR target not prospectively bound to log_SFR_Ha")
    seen=set()
    descendants={str(x).casefold() for x in target_descendants}
    for raw in names:
        name=str(raw).strip().casefold()
        if name in seen:
            raise LeakageGateError(f"duplicate predictor {name}")
        seen.add(name)
        if name in DIRECT_TARGET_ALIASES or name in descendants or "sfr_ha" in name:
            raise LeakageGateError(f"target-derived predictor forbidden: {name}")
    if not seen:raise LeakageGateError("empty predictor set")
    return tuple(sorted(seen))

def assert_group_disjoint(train_ids,test_ids):
    tr=set(train_ids);te=set(test_ids)
    if not tr or not te:raise LeakageGateError("empty split")
    if len(tr.intersection(te)):
        raise LeakageGateError("shared target/galaxy/sky group across train/test")
    return True

def diagnostic_baseline_pipeline():
    """Fixture-only training-fold pipeline; NEVER fit preprocessing globally."""
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import Ridge
    return Pipeline([("imputer",SimpleImputer(strategy="median")),
                     ("scaler",StandardScaler()),
                     ("estimator",Ridge(alpha=1.0))])

def prohibit_sfr_inference():
    raise LeakageGateError(
        "EXP-CTRL-A02 / EXP-SFR-A01 not preregistered: no frozen Pipe3D source, "
        "prediction target, feature inventory, sky/group split or arithmetic null.")
