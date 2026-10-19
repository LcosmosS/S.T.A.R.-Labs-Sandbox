"""Synthetic no-data fixtures for matching and SFR leakage prohibitions."""
import math
import numpy as np
import pytest
from src.data.spherical_match_candidate import (
    CrossmatchGateError, angular_separation_arcsec, enumerate_candidates,
    unique_nonambiguous_pairs, prohibit_controlled_matching)
from src.quality.sfr_leakage_gate import (
    LeakageGateError,validate_feature_names,assert_group_disjoint,
    diagnostic_baseline_pipeline,prohibit_sfr_inference)

def test_ra_wrap_and_sub_arcsec_geometry():
    assert abs(angular_separation_arcsec(359.9999,0,0.0001,0)-0.72) < 1e-8
    assert angular_separation_arcsec(0,90,180,90) < 1e-6
    pairs=enumerate_candidates([[359.9999,0]],[[0.0001,0]])
    assert len(pairs)==1 and pairs[0][2] < 1

def test_near_pole_and_two_arcsecond_boundary():
    assert angular_separation_arcsec(0,89.999,180,89.999) < 8
    near=[[0.,0.],[30.,0.]]
    right=[[0.,1./3600],[30.,10./3600]]
    assert len(enumerate_candidates(near,right)) == 1
    with pytest.raises(CrossmatchGateError,match="primary candidate radius"):
        enumerate_candidates(near,right,radius_arcsec=3.0)

def test_ambiguity_is_rejected_not_first_match():
    left=[[10.,0.],[10.0001,0.],[30.,0.]]
    right=[[10.00002,0.],[30.00001,0.]]
    accepted,ambiguous=unique_nonambiguous_pairs(left,right)
    assert len(accepted)==1 and accepted[0][0]==2
    assert len(ambiguous)==2

def test_coordinate_bounds_and_source_provenance_hard_stop():
    with pytest.raises(CrossmatchGateError,match="outside"):
        enumerate_candidates([[360.,0.]],[[0.,0.]])
    with pytest.raises(CrossmatchGateError,match="nonfinite"):
        enumerate_candidates([[float("nan"),0.]],[[0.,0.]])
    with pytest.raises(CrossmatchGateError,match="planned"):
        prohibit_controlled_matching()

def test_target_derived_alias_and_group_leakage_guards():
    assert "log_mass" in validate_feature_names(["log_Mass","z"])
    for name in ["log_SFR_Ha_raw","flux_Ha","sfr","my_sfr_ha_proxy"]:
        with pytest.raises(LeakageGateError,match="target-derived"):
            validate_feature_names(["z",name])
    with pytest.raises(LeakageGateError,match="shared"):
        assert_group_disjoint(["manga-1","manga-2"],["manga-2"])
    assert assert_group_disjoint(["tile-A"],["tile-B"])

def test_imputation_and_scaling_are_fit_inside_train_pipeline_only():
    model=diagnostic_baseline_pipeline()
    assert list(model.named_steps)==["imputer","scaler","estimator"]
    x=np.asarray([[1.,2.],[2.,float("nan")],[3.,4.],[4.,6.]])
    y=np.asarray([1.,2.,3.,4.])
    model.fit(x[:3],y[:3])
    assert not np.isnan(model.predict(x[3:])).any()
    with pytest.raises(LeakageGateError,match="not preregistered"):
        prohibit_sfr_inference()
