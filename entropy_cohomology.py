import pandas as pd
import numpy as np
import warnings
from astropy.cosmology import Planck18 as cosmo
from astropy import units as u
from sage.all import EllipticCurve, QQ, factor, pari
from sage.parallel.decorate import parallel
import matplotlib.pyplot as plt
from matplotlib import animation
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
import altair as alt
import plotly.express as px
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, classification_report
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor, StackingClassifier, StackingRegressor
from sklearn.cluster import DBSCAN, KMeans
from sklearn.impute import KNNImputer
from sklearn.inspection import permutation_importance
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.neighbors import KernelDensity
from datetime import datetime
import threading
from contextlib import redirect_stderr
import os
try:
    from xgboost import XGBClassifier, XGBRegressor
except ImportError:
    XGBClassifier = XGBRegressor = None
try:
    from lightgbm import LGBMClassifier, LGBMRegressor
except ImportError:
    LGBMClassifier = LGBMRegressor = None
try:
    from catboost import CatBoostClassifier, CatBoostRegressor
except ImportError:
    CatBoostClassifier = CatBoostRegressor = None
try:
    from pysr import PySRRegressor
except ImportError:
    PySRRegressor = None
try:
    from gplearn.genetic import SymbolicRegressor
except ImportError:
    SymbolicRegressor = None
try:
    from optuna import create_study
except ImportError:
    create_study = None
try:
    import cypari2
except ImportError:
    print("cypari2 not installed. Run: mamba install cypari2 -c conda-forge")
    exit(1)
try:
    from gudhi.weighted_rips_complex import WeightedRipsComplex
    from gudhi import plot_persistence_diagram
    import gudhi
except ImportError:
    print("gudhi not installed. Run: pip install gudhi")
    gudhi = None
from scipy.spatial.distance import cdist
import multiprocessing as mp
import gc
from tqdm import tqdm
import logging
import csv

# Configuration
INPUT_FILE = 'GalSpecExtra.csv'
OUTPUT_PLOT_PREFIX = 'final_two_tier_synthesis_v49'
CHUNKSIZE = 10000  # Optimized for 10-12GB RAM
ROW_LIMIT = 866000
TARGET_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
REQUIRED_COLUMNS = ['objid', 'ra', 'dec', 'z', 'logmass', 'petrorad_r', 'metallicity']
T_COSMO = 17.18
REG_COSMO = 2.51
KAPPA = 1.0
SELMER_BOUND = 20
MAX_CONDUCTOR = 10**20
KB = 1.380649e-23  # Boltzmann constant (J/K)
COHOMOLOGY_WEIGHT = 1e-3
ENTROPY_GRADIENT_WEIGHT = 1e-2
MAX_COHOM_POINTS = 1000000
MIN_LOGMASS = 10.5
PARI_STACK_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
PARI_STACK_MAX = 4 * 1024 * 1024 * 1024  # 4GB for retries
DISCRIMINANT_THRESHOLD = 10**16  # Increased to allow more curves

# Logging setup
logging.basicConfig(filename='debug.log', level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only show WARNING and above in terminal
logging.getLogger('').addHandler(console_handler)

analysis_logger = logging.getLogger('analysis')
analysis_handler = logging.FileHandler('analysis.log')
analysis_handler.setLevel(logging.INFO)
analysis_logger.addHandler(analysis_handler)

debug_csv_file = 'debug_log.csv'
analysis_csv_file = 'analysis_log.csv'

with open(debug_csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Timestamp', 'Level', 'Message'])
with open(analysis_csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Timestamp', 'Level', 'Message', 'Summary'])

class CSVHandler(logging.Handler):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
    def emit(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        msg = self.format(record)
        summary = getattr(record, 'summary', '')
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, record.levelname, msg, summary])

debug_csv_handler = CSVHandler(debug_csv_file)
debug_csv_handler.setLevel(logging.DEBUG)
logging.getLogger('').addHandler(debug_csv_handler)
analysis_csv_handler = CSVHandler(analysis_csv_file)
analysis_csv_handler.setLevel(logging.INFO)
analysis_logger.addHandler(analysis_csv_handler)

logging_lock = threading.Lock()

def print_step(step_num, step_name, summary=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[STEP {step_num}] {timestamp} - {step_name}")
    logging.info(f"Step {step_num}: {step_name}")
    if summary is not None:
        print(f"[SUMMARY {step_num}] {step_name} completed.")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        analysis_logger.info(f"Step {step_num} Summary: {summary}", extra={'summary': str(summary)})

def impute_input_features(df):
    print_step(5, "Impute Input Features")
    df = df.copy()
    input_cols = ['logmass', 'metallicity', 'petrorad_r', 'ra', 'dec', 'z']
    available_cols = [col for col in input_cols if col in df.columns]
    summary = {'Rows Before': len(df), 'NaN Counts Before': df[available_cols].isna().sum().to_dict()}
    
    # Quick median imputation for small chunks to save memory
    for col in available_cols:
        if col in df.columns and df[col].isna().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logging.debug(f"impute_input_features: Filled NaN in {col} with median {median_val}")
    
    # KNN imputation for remaining NaNs if feasible
    try:
        imputer = KNNImputer(n_neighbors=5, weights='distance')
        df[available_cols] = imputer.fit_transform(df[available_cols])
        logging.debug(f"impute_input_features: Applied KNN imputation to {available_cols}")
    except Exception as e:
        logging.warning(f"impute_input_features: KNN imputation failed - {str(e)}. Falling back to median.")
        for col in available_cols:
            if col in df.columns and df[col].isna().any():
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                logging.debug(f"impute_input_features: Fallback filled NaN in {col} with median {median_val}")
    
    summary['NaN Counts After'] = df[available_cols].isna().sum().to_dict()
    analysis_logger.info(f"impute_input_features: {summary}", extra={'summary': str(summary)})
    return df, summary

def impute_derived_features(df, feature_cols):
    print_step(5, "Impute Derived Features")
    df = df.copy()
    available_cols = [col for col in feature_cols if col in df.columns]
    summary = {'Rows Before': len(df), 'NaN Counts Before': df[available_cols].isna().sum().to_dict()}
    
    # Median imputation for numerical derived features
    for col in available_cols:
        if col in df.columns and df[col].isna().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logging.debug(f"impute_derived_features: Filled NaN in {col} with median {median_val}")
    
    # KNN imputation for remaining NaNs
    try:
        imputer = KNNImputer(n_neighbors=5, weights='distance')
        df[available_cols] = imputer.fit_transform(df[available_cols])
        logging.debug(f"impute_derived_features: Applied KNN imputation to {available_cols}")
    except Exception as e:
        logging.warning(f"impute_derived_features: KNN imputation failed - {str(e)}. Falling back to median.")
        for col in available_cols:
            if col in df.columns and df[col].isna().any():
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                logging.debug(f"impute_derived_features: Fallback filled NaN in {col} with median {median_val}")
    
    summary['NaN Counts After'] = df[available_cols].isna().sum().to_dict()
    analysis_logger.info(f"impute_derived_features: {summary}", extra={'summary': str(summary)})
    return df

def estimate_entropy(row):
    logmass = row['logmass']
    petrorad_r = row['petrorad_r']
    metallicity = row['metallicity']
    if not all(np.isfinite([logmass, petrorad_r, metallicity])):
        return np.nan, {'Entropy': 'NaN', 'Reason': 'Invalid input'}
    entropy = KB * (logmass * 1e6 / (petrorad_r * 3.0857e16)**3) * metallicity
    summary = {'Entropy': entropy, 'Logmass': logmass, 'Petrorad_r': petrorad_r, 'Metallicity': metallicity}
    return entropy, summary

def compute_entropy_gradient(df):
    print_step(7, "Compute Entropy Gradient")
    df = df.copy()
    coords = df[['ra', 'dec', 'z']].values
    entropy = df['entropy'].values
    valid_idx = np.isfinite(coords).all(axis=1) & np.isfinite(entropy)
    coords = coords[valid_idx]
    entropy = entropy[valid_idx]
    if len(coords) < 2:
        df['entropy_gradient'] = np.nan
        summary = {'Valid Rows': len(coords), 'Status': 'Insufficient data'}
        return df, np.array([np.nan] * len(df)), summary
    kde = KernelDensity(bandwidth=0.1, kernel='gaussian')
    kde.fit(coords, sample_weight=entropy)
    log_density = kde.score_samples(coords)
    h = 0.01
    grad = np.zeros_like(coords)
    for i in range(coords.shape[1]):
        coords_pos = coords.copy()
        coords_pos[:, i] += h
        log_density_pos = kde.score_samples(coords_pos)
        grad[:, i] = (log_density_pos - log_density) / h
    entropy_gradient = np.linalg.norm(grad, axis=1)
    df.loc[df.index[valid_idx], 'entropy_gradient'] = entropy_gradient
    df['entropy_gradient'] = df['entropy_gradient'].where(df['entropy_gradient'].notna(), np.nan)
    summary = {
        'Valid Rows': len(coords),
        'Entropy Gradient Mean': np.nanmean(entropy_gradient),
        'Entropy Gradient Std': np.nanstd(entropy_gradient)
    }
    analysis_logger.info(f"compute_entropy_gradient: {summary}", extra={'summary': str(summary)})
    return df, entropy_gradient, summary

def compute_cohomology(df):
    print_step(21, "Compute Cohomology")
    df = df.copy()
    if gudhi is None:
        logging.warning("compute_cohomology: gudhi not installed. Returning NaN for Betti numbers.")
        df['betti_1'] = np.nan
        return df, np.array([np.nan] * len(df)), {'Status': 'gudhi not installed'}
    coords = df[['ra', 'dec', 'z']].dropna()
    if len(coords) < 2:
        logging.warning("compute_cohomology: Not enough valid coordinates for cohomology")
        df['betti_1'] = np.nan
        return df, np.array([np.nan] * len(df)), {'Status': 'Insufficient data'}
    if len(coords) > MAX_COHOM_POINTS:
        coords = coords.sample(MAX_COHOM_POINTS, random_state=42)
        logging.info(f"compute_cohomology: Subsampled to {MAX_COHOM_POINTS} points")
    points = coords.values
    scaler = StandardScaler()
    points = scaler.fit_transform(points)
    weights = df.loc[coords.index, 'entropy'].values
    weights = np.where(np.isfinite(weights), weights, np.median(weights[np.isfinite(weights)]))
    dist = cdist(points, points)
    max_filtration = np.max(dist) if np.isfinite(dist).any() else 1.0
    w_rips = WeightedRipsComplex(distance_matrix=dist, weights=weights, max_filtration=max_filtration)
    simplex_tree = w_rips.create_simplex_tree(max_dimension=2)
    persistence = simplex_tree.persistence()
    betti_1 = sum(1 for dim, (birth, death) in persistence if dim == 1 and death != float('inf'))
    df['betti_1'] = np.nan
    df.loc[coords.index, 'betti_1'] = betti_1
    summary = {
        'Valid Rows': len(coords),
        'Betti_1': betti_1,
        'Points Used': len(points)
    }
    analysis_logger.info(f"compute_cohomology: {summary}", extra={'summary': str(summary)})
    return df, np.array([betti_1] * len(df)), summary

def compute_kde_features(df, feature_x, feature_y):
    print_step(9, "Compute KDE Features")
    df = df.copy()
    data = df[[feature_x, feature_y]].dropna()
    if data.empty:
        logging.warning(f"compute_kde_features: No valid data for {feature_x} and {feature_y}")
        df[f'kde_{feature_x}_{feature_y}'] = np.nan
        return df, np.array([np.nan] * len(df)), {'Status': 'No valid data'}
    kde = KernelDensity(bandwidth=0.1, kernel='gaussian')
    kde.fit(data)
    log_dens = kde.score_samples(data)
    df.loc[data.index, f'kde_{feature_x}_{feature_y}'] = log_dens
    summary = {
        'Valid Rows': len(data),
        'KDE Mean': np.nanmean(log_dens),
        'KDE Std': np.nanstd(log_dens)
    }
    analysis_logger.info(f"compute_kde_features: {summary}", extra={'summary': str(summary)})
    return df, log_dens, summary

def calculate_distance_mpc(z):
    try:
        if not np.isfinite(z) or z <= 0:
            return np.nan, {'Distance': 'NaN', 'Reason': 'Invalid z'}
        dist = cosmo.comoving_distance(z).value
        return dist, {'Distance': dist, 'z': z}
    except Exception as e:
        logging.error(f"calculate_distance_mpc: Error for z={z} - {str(e)}")
        return np.nan, {'Distance': 'NaN', 'Reason': str(e)}

def convert_logmass_to_sm(logmass):
    if not np.isfinite(logmass):
        return np.nan
    return 10**logmass

def estimate_radius_ly(petrorad_r, distance_mpc):
    if not all(np.isfinite([petrorad_r, distance_mpc])):
        return np.nan
    return petrorad_r * distance_mpc * 206265 / 3.0857e16

@parallel(ncpus=6)
def compute_3selmer_rank(args):
    delta, conductor, logmass, entropy, betti_1, entropy_gradient, pari = args
    entropy = 0 if np.isnan(entropy) else entropy
    betti_1 = 0 if np.isnan(betti_1) else betti_1
    entropy_gradient = 0 if np.isnan(entropy_gradient) else entropy_gradient
    if not all(np.isfinite(x) for x in [delta, conductor, logmass]):
        logging.debug(f"compute_3selmer_rank: Skipped - Invalid delta={delta}, conductor={conductor}, logmass={logmass}")
        return np.nan, 'invalid_input', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'invalid_input', 'Evidence': {}}

    invalid_output_count = 0
    singular_curve_count = 0

    def try_compute_rank(stack_size):
        nonlocal invalid_output_count, singular_curve_count
        with open('sagemath_output.log', 'a') as f, redirect_stderr(f):
            with logging_lock:
                try:
                    pari.allocatemem(stack_size)
                    delta_scaled = delta / 1e6
                    conductor_scaled = min(int(delta_scaled**2), MAX_CONDUCTOR)
                    a = -int(delta_scaled / 1e2)
                    b = int(delta_scaled**2 / 1e4) + entropy * logmass + COHOMOLOGY_WEIGHT * betti_1 + ENTROPY_GRADIENT_WEIGHT * entropy_gradient
                    curve_name = f"a={a},b={b}"
                    discriminant = 4 * a**3 + 27 * b**2
                    if abs(discriminant) > DISCRIMINANT_THRESHOLD:
                        logging.debug(f"compute_3selmer_rank: Skipped - Large discriminant={discriminant} for curve {curve_name}")
                        return np.nan, 'large_discriminant', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'large_discriminant', 'Evidence': {}, 'Curve_Name': curve_name}
                    if conductor_scaled > MAX_CONDUCTOR:
                        logging.debug(f"compute_3selmer_rank: Skipped - Scaled conductor={conductor_scaled} > MAX_CONDUCTOR")
                        return np.nan, 'large_conductor', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'large_conductor', 'Evidence': {}, 'Curve_Name': curve_name}
                    if discriminant == 0:
                        if singular_curve_count < 5:
                            logging.warning(f"compute_3selmer_rank: Singular curve for {curve_name}, discriminant={discriminant}")
                            singular_curve_count += 1
                        return np.nan, 'singular_curve', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'singular_curve', 'Evidence': {}, 'Curve_Name': curve_name}
                    E = EllipticCurve(QQ, [0, 0, 0, a, b]).minimal_model()
                    evidence = {}
                    try:
                        rank_standard = E.rank(only_use_mwrank=False)
                        evidence['standard_rank'] = {'value': rank_standard, 'status': 'success'}
                    except Exception as e:
                        rank_standard = np.nan
                        evidence['standard_rank'] = {'value': np.nan, 'status': f'error_{str(e)}'}
                    try:
                        selmer_rank = E.selmer_rank()
                        evidence['selmer_rank'] = {'value': selmer_rank, 'status': 'success'}
                    except Exception as e:
                        selmer_rank = np.nan
                        evidence['selmer_rank'] = {'value': np.nan, 'status': f'error_{str(e)}'}
                    try:
                        two_desc = E.two_descent(second_limit=200, verbose=0)
                        if isinstance(two_desc, tuple) and len(two_desc) >= 3 and all(isinstance(x, (int, float)) for x in two_desc[:2]):
                            rank_lower, rank_upper, _ = two_desc[:3]
                            evidence['two_descent'] = {'lower_bound': rank_lower, 'upper_bound': rank_upper, 'status': 'success'}
                        else:
                            output_type = type(two_desc).__name__
                            if invalid_output_count < 5:
                                logging.warning(f"compute_3selmer_rank: Invalid two_descent output for {curve_name}: type={output_type}")
                                invalid_output_count += 1
                            evidence['two_descent'] = {'lower_bound': np.nan, 'upper_bound': np.nan, 'status': f'invalid_output_{output_type}'}
                            rank_lower = selmer_rank if not np.isnan(selmer_rank) else rank_standard if not np.isnan(rank_standard) else np.nan
                            rank_upper = rank_lower
                    except Exception as e:
                        evidence['two_descent'] = {'lower_bound': np.nan, 'upper_bound': np.nan, 'status': f'error_{str(e)}'}
                        rank_lower = selmer_rank if not np.isnan(selmer_rank) else rank_standard if not np.isnan(rank_standard) else np.nan
                        rank_upper = rank_lower
                    try:
                        torsion = E.torsion_subgroup().order()
                        disc = E.discriminant()
                        evidence['torsion'] = {'value': torsion, 'status': 'success'}
                        evidence['discriminant'] = {'value': disc, 'status': 'success'}
                    except Exception as e:
                        torsion = np.nan
                        disc = np.nan
                        evidence['torsion'] = {'value': np.nan, 'status': f'error_{str(e)}'}
                        evidence['discriminant'] = {'value': np.nan, 'status': f'error_{str(e)}'}
                    valid_ranks = [r for r in [
                        evidence.get('standard_rank', {}).get('value'),
                        evidence.get('selmer_rank', {}).get('value'),
                        evidence.get('two_descent', {}).get('lower_bound')
                    ] if not np.isnan(r) and r is not None]
                    final_rank = int(np.median(valid_ranks)) if valid_ranks else np.nan
                    status = 'success' if valid_ranks and final_rank <= SELMER_BOUND else 'no_valid_ranks' if not valid_ranks else 'high_rank'
                    j_inv = E.j_invariant() if evidence['discriminant'].get('status') == 'success' else np.nan
                    summary = {
                        'Rank': final_rank,
                        'Status': status,
                        'Logmass': logmass,
                        'Delta_Scaled': delta_scaled,
                        'Conductor_Scaled': conductor_scaled,
                        'Entropy': entropy,
                        'Betti_1': betti_1,
                        'Entropy_Gradient': entropy_gradient,
                        'Evidence': evidence,
                        'Curve_Name': curve_name,
                        'Stack_Size_Used': stack_size
                    }
                    analysis_logger.info(f"compute_3selmer_rank: {summary}", extra={'summary': str(summary)})
                    pari.allocatemem(0)
                    gc.collect()
                    return final_rank, status, torsion, j_inv, disc, summary
                except Exception as e:
                    logging.error(f"compute_3selmer_rank: Error for {curve_name} - {str(e)}")
                    pari.allocatemem(0)
                    gc.collect()
                    return np.nan, f'error_{str(e)}', np.nan, np.nan, np.nan, {
                        'Rank': 'NaN', 'Status': f'error_{str(e)}', 'Evidence': {}, 'Curve_Name': curve_name, 'Stack_Size_Used': stack_size
                    }

    curve_name = "undefined"
    result = try_compute_rank(PARI_STACK_SIZE)
    if result[1].startswith('error_pari_stack'):
        result = try_compute_rank(PARI_STACK_MAX)
    return np.nan, 'parallel_wrapper', np.nan, np.nan, np.nan, result

def compute_mappings(row, pari):
    reg_cosmo = row['logmass'] * REG_COSMO * KAPPA if np.isfinite(row['logmass']) else np.nan
    t_cosmo = row['petrorad_r'] * T_COSMO * KAPPA if np.isfinite(row['petrorad_r']) else np.nan
    delta = row['logmass'] * 1e6 if np.isfinite(row['logmass']) else np.nan
    omega = row['petrorad_r'] * 1e3 if np.isfinite(row['petrorad_r']) else np.nan
    conductor = delta**2 if np.isfinite(delta) else np.nan
    j_invariant = row['metallicity'] * 1e4 if np.isfinite(row['metallicity']) else np.nan
    tr_p1 = float(factor(int(delta))[0][0]) if np.isfinite(delta) and delta > 0 else np.nan
    tr_p2 = float(factor(int(delta * 2))[0][0]) if np.isfinite(delta) and delta > 0 else np.nan
    tr_p3 = float(factor(int(delta * 3))[0][0]) if np.isfinite(delta) and delta > 0 else np.nan
    var_ap = np.var([tr_p1, tr_p2, tr_p3]) if all(np.isfinite([tr_p1, tr_p2, tr_p3])) else np.nan
    sato_tate = float(TARGET_PRIMES[0] * np.arccos(tr_p1 / (2 * np.sqrt(TARGET_PRIMES[0])))) if np.isfinite(tr_p1) and tr_p1 != 0 else np.nan
    isogeny_count = 1
    min_isogeny_deg = 1
    torsion_type = 1
    entropy, entropy_summary = estimate_entropy(row)
    betti_1 = row.get('betti_1', np.nan)
    entropy_gradient = row.get('entropy_gradient', np.nan)
    args = (delta, conductor, row['logmass'], entropy, betti_1, entropy_gradient, pari)
    try:
        parallel_result = compute_3selmer_rank(args)
        if isinstance(parallel_result, tuple) and len(parallel_result) == 2:
            _, result = parallel_result
        else:
            result = parallel_result
        if isinstance(result, tuple) and len(result) == 6:
            selmer_rank, selmer_status, torsion, j_inv, disc, selmer_summary = result
        else:
            selmer_rank = np.nan
            selmer_status = 'parallel_error'
            torsion = np.nan
            j_inv = np.nan
            disc = np.nan
            selmer_summary = {'Rank': 'NaN', 'Status': 'parallel_error', 'Evidence': {}}
            logging.warning(f"compute_mappings: Invalid parallel result format: {result}")
    except Exception as e:
        logging.error(f"compute_mappings: Parallel computation failed - {str(e)}")
        selmer_rank = np.nan
        selmer_status = f'error_{str(e)}'
        torsion = np.nan
        j_inv = np.nan
        disc = np.nan
        selmer_summary = {'Rank': 'NaN', 'Status': f'error_{str(e)}', 'Evidence': {}}
    summary = {
        'Reg_Cosmo': reg_cosmo,
        'T_Cosmo': t_cosmo,
        'Log_Delta': np.log(abs(delta)) if np.isfinite(delta) and delta > 0 else np.nan,
        'Selmer_Rank': selmer_rank,
        'Selmer_Status': selmer_status
    }
    return pd.Series({
        'reg_cosmo': reg_cosmo,
        't_cosmo': t_cosmo,
        'log_delta': np.log(abs(delta)) if np.isfinite(delta) and delta > 0 else np.nan,
        'log_omega': np.log(abs(omega)) if np.isfinite(omega) and omega > 0 else np.nan,
        'log_torsion': np.log(1 + torsion) if np.isfinite(torsion) else np.nan,
        'log_conductor': np.log(abs(conductor)) if np.isfinite(conductor) and conductor > 0 else np.nan,
        'real_log_j': np.log(abs(j_invariant)) if np.isfinite(j_invariant) and j_invariant != 0 else np.nan,
        'imag_log_j': 0.0,
        'tr_p1': tr_p1,
        'var_ap': var_ap,
        'sato_tate': sato_tate,
        'isogeny_count': isogeny_count,
        'log_min_isogeny': np.log(min_isogeny_deg) if min_isogeny_deg != 0 else np.nan,
        'log_torsion_type': np.log(1 + torsion_type),
        'selmer_rank': selmer_rank,
        'selmer_status': selmer_status,
        'torsion': torsion,
        'j_invariant': j_inv,
        'discriminant': disc,
        'entropy': entropy,
        'betti_1': betti_1,
        'entropy_gradient': entropy_gradient
    }), summary

def analyze_generator_structure(coords):
    if pd.isna(coords):
        return {'type': 'unknown', 'structure': 'unknown'}, {'Type': 'unknown', 'Structure': 'unknown'}
    x, y = coords if isinstance(coords, tuple) else (np.nan, np.nan)
    if pd.isna(x) or pd.isna(y):
        return {'type': 'unknown', 'structure': 'unknown'}, {'Type': 'unknown', 'Structure': 'unknown'}
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and float(x).is_integer() and float(y).is_integer():
        return {'type': 'unknown', 'structure': 'integer'}, {'Type': 'unknown', 'Structure': 'integer'}
    denom_x = x.denominator() if hasattr(x, 'denominator') else 1
    denom_y = y.denominator() if hasattr(y, 'denominator') else 1
    factors_x = factor(denom_x) if denom_x != 1 else []
    if len(factors_x) == 1 and len(factors_x[0][0].prime_factors()) == 1:
        return {'type': 'unknown', 'structure': 'power_of_prime'}, {'Type': 'unknown', 'Structure': 'power_of_prime'}
    return {'type': 'unknown', 'structure': 'other_sequence'}, {'Type': 'unknown', 'Structure': 'other_sequence'}

def preprocess_clustering_features(X_struct, feature_cols):
    X_struct = X_struct.copy()
    imputer = KNNImputer(n_neighbors=5, weights='distance')
    available_cols = [col for col in feature_cols if col in X_struct.columns]
    X_struct[available_cols] = imputer.fit_transform(X_struct[available_cols])
    analysis_logger.info(f"preprocess_clustering_features: Imputed NaN in {available_cols}", extra={'summary': f"Imputed NaN in {available_cols}"})
    return X_struct

def optimize_catboost_classifier(X, y, n_trials=50):
    if CatBoostClassifier is None or create_study is None:
        logging.warning("CatBoost or Optuna not installed. Skipping optimization.")
        return None
    def objective(trial):
        params = {
            'iterations': trial.suggest_int('iterations', 100, 1000),
            'depth': trial.suggest_int('depth', 4, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 10)
        }
        model = CatBoostClassifier(**params, verbose=0)
        return cross_val_score(model, X, y, cv=5, n_jobs=-1).mean()
    study = create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials, n_jobs=-1)
    return study.best_params

def optimize_catboost_regressor(X, y, n_trials=50):
    if CatBoostRegressor is None or create_study is None:
        logging.warning("CatBoost or Optuna not installed. Skipping optimization.")
        return None
    def objective(trial):
        params = {
            'iterations': trial.suggest_int('iterations', 100, 1000),
            'depth': trial.suggest_int('depth', 4, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 10)
        }
        model = CatBoostRegressor(**params, verbose=0)
        return cross_val_score(model, X, y, cv=5, scoring='r2', n_jobs=-1).mean()
    study = create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials, n_jobs=-1)
    return study.best_params

def run_symbolic_regression(X, y, feature_cols, method='pysr'):
    available_cols = [col for col in feature_cols if col in X.columns]
    if method == 'pysr' and PySRRegressor:
        model = PySRRegressor(
            niterations=40,
            binary_operators=["+", "-", "*", "/"],
            unary_operators=["log", "exp", "sqrt"],
            maxsize=20,
            model_selection="best"
        )
        model.fit(X[available_cols], y)
        analysis_logger.info(f"PySR Equations:\n {model.equations_}", extra={'summary': str(model.equations_)})
        return model
    elif method == 'gplearn' and SymbolicRegressor:
        model = SymbolicRegressor(
            population_size=1000,
            generations=20,
            function_set=('add', 'sub', 'mul', 'div', 'log', 'sqrt'),
            metric='mse',
            random_state=42
        )
        model.fit(X[available_cols], y)
        analysis_logger.info(f"GPlearn Equation:\n {model._program}", extra={'summary': str(model._program)})
        return model
    else:
        logging.warning(f"{method} not installed. Skipping symbolic regression.")
        return None

def statistical_mechanics_test(df, output_prefix=OUTPUT_PLOT_PREFIX):
    N = len(df)
    expected_T_cosmo = np.sqrt(N)
    fluctuation = abs(T_COSMO - expected_T_cosmo) / expected_T_cosmo
    summary = {
        'N': N,
        'Expected_T_cosmo': expected_T_cosmo,
        'Observed_T_cosmo': T_COSMO,
        'Relative_Fluctuation': fluctuation
    }
    plt.figure(figsize=(10, 6))
    plt.scatter([N], [T_COSMO], color='blue', label='Observed T_cosmo')
    plt.plot([N], [expected_T_cosmo], 'r*', label='Expected T_cosmo = sqrt(N)')
    plt.xlabel('Number of Galaxies (N)')
    plt.ylabel('T_cosmo')
    plt.title('Statistical Mechanics: T_cosmo vs sqrt(N)')
    plt.legend()
    plt.savefig(f'{output_prefix}_stat_mech_test.png')
    plt.close()
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    def animate(i):
        ax.clear()
        n = 1000 + i * 1000
        ax.scatter([n], [np.sqrt(n)], color='red', label='Expected T_cosmo')
        ax.scatter([N], [T_COSMO], color='blue', label='Observed T_cosmo')
        ax.set_xlabel('Number of Galaxies (N)')
        ax.set_ylabel('T_cosmo')
        ax.set_title('T_cosmo Evolution with N')
        ax.legend()
    anim = animation.FuncAnimation(fig, animate, frames=50, interval=100, blit=False)
    anim.save(f'{output_prefix}_stat_mech_animation.mp4', writer='ffmpeg', fps=30)
    plt.close()
    analysis_logger.info(f"statistical_mechanics_test: {summary}", extra={'summary': str(summary)})
    return summary

def tully_fisher_test(df, feature_cols, output_prefix=OUTPUT_PLOT_PREFIX):
    X_tf = df[feature_cols]
    y_tf = df['logmass']
    valid_idx = y_tf.notna()
    X_tf = X_tf[valid_idx]
    y_tf = y_tf[valid_idx]
    summary = {'Rows Dropped': len(df) - len(X_tf)}
    if X_tf.empty:
        logging.warning("tully_fisher_test: No valid data")
        summary['Status'] = 'No valid data'
        return summary
    catboost_params_reg = optimize_catboost_regressor(X_tf, y_tf) if CatBoostRegressor and create_study else None
    regressors = [
        ('RandomForest', RandomForestRegressor(random_state=42, n_jobs=-1)),
        ('HistGradientBoosting', HistGradientBoostingRegressor(random_state=42))
    ]
    if XGBRegressor:
        regressors.append(('XGBoost', XGBRegressor(random_state=42, n_jobs=-1)))
    if LGBMRegressor:
        regressors.append(('LightGBM', LGBMRegressor(random_state=42, n_jobs=-1)))
    if CatBoostRegressor and catboost_params_reg:
        regressors.append(('CatBoost', CatBoostRegressor(**catboost_params_reg, verbose=0)))
    pipeline = Pipeline([
        ('scaler', StandardScaler(with_mean=False)),
        ('regressor', StackingRegressor(estimators=regressors, final_estimator=HistGradientBoostingRegressor(random_state=42), n_jobs=-1))
    ])
    pipeline.fit(X_tf, y_tf)
    tf_r2 = cross_val_score(pipeline, X_tf, y_tf, cv=5, scoring='r2', n_jobs=-1).mean()
    tf_perm_importance = permutation_importance(pipeline.named_steps['regressor'], X_tf, y_tf, n_repeats=10, random_state=42, n_jobs=-1)
    tf_feature_importance = pd.Series(tf_perm_importance.importances_mean, index=X_tf.columns).sort_values(ascending=False)
    tf_feature_importance.to_csv(f'{output_prefix}_tully_fisher_feature_importance.csv')
    plt.figure(figsize=(10, 6))
    sns.barplot(x=tf_feature_importance.values, y=tf_feature_importance.index)
    plt.title('Tully-Fisher Feature Importance')
    plt.savefig(f'{output_prefix}_tully_fisher_feature_importance.png')
    plt.close()
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    y_pred = pipeline.predict(X_tf)
    def animate(i):
        ax.clear()
        ax.scatter(y_tf[:i*100+100], y_pred[:i*100+100], alpha=0.5)
        ax.plot([y_tf.min(), y_tf.max()], [y_tf.min(), y_tf.max()], 'r--')
        ax.set_xlabel('Actual Logmass')
        ax.set_ylabel('Predicted Logmass')
        ax.set_title(f'Tully-Fisher Prediction (R2 = {tf_r2:.2f})')
    anim = animation.FuncAnimation(fig, animate, frames=50, interval=100, blit=False)
    anim.save(f'{output_prefix}_tully_fisher_animation.mp4', writer='ffmpeg', fps=30)
    plt.close()
    for method in ['pysr', 'gplearn']:
        sym_reg_tf = run_symbolic_regression(X_tf, y_tf, feature_cols, method)
        if sym_reg_tf:
            getattr(sym_reg_tf, 'equations_', pd.DataFrame()).to_csv(f'{output_prefix}_symbolic_regression_tully_fisher_{method}.csv')
    summary.update({'R2': tf_r2, 'Top Features': tf_feature_importance.head(5).to_dict()})
    analysis_logger.info(f"tully_fisher_test: R² = {tf_r2}", extra={'summary': str(summary)})
    return summary

def math_physics_unification_test(df, output_prefix=OUTPUT_PLOT_PREFIX):
    conductor_counts = df['log_conductor'].value_counts()
    prime_divisibility = {p: sum(df['log_conductor'].dropna() % np.log(p) < 0.1) for p in TARGET_PRIMES}
    summary = {
        'Conductor_Distribution': conductor_counts.to_dict(),
        'Prime_Divisibility': prime_divisibility
    }
    plt.figure(figsize=(10, 6))
    sns.barplot(x=list(prime_divisibility.keys()), y=list(prime_divisibility.values()))
    plt.xlabel('Prime')
    plt.ylabel('Number of Curves Divisible (log scale)')
    plt.title('Math-Physics Unification: Conductor Divisibility by Primes')
    plt.savefig(f'{output_prefix}_math_physics_unification.png')
    plt.close()
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    def animate(i):
        ax.clear()
        prime_subset = TARGET_PRIMES[:i+1]
        counts = [prime_divisibility[p] for p in prime_subset]
        ax.bar(prime_subset, counts)
        ax.set_xlabel('Prime')
        ax.set_ylabel('Number of Curves Divisible')
        ax.set_title('Conductor Divisibility Evolution')
    anim = animation.FuncAnimation(fig, animate, frames=len(TARGET_PRIMES), interval=200, blit=False)
    anim.save(f'{output_prefix}_math_physics_unification_animation.mp4', writer='ffmpeg', fps=30)
    plt.close()
    analysis_logger.info(f"math_physics_unification_test: {summary}", extra={'summary': str(summary)})
    return summary

def anthropic_principle_test(df, output_prefix=OUTPUT_PLOT_PREFIX):
    rank_counts = df['selmer_rank'].value_counts()
    stability_ratio = rank_counts.get(1, 0) / len(df) if len(df) > 0 else 0
    summary = {
        'Rank_Distribution': rank_counts.to_dict(),
        'Stability_Ratio': stability_ratio,
        'High_Rank_Count': sum(rank_counts.get(r, 0) for r in range(3, int(df['selmer_rank'].max()) + 1))
    }
    plt.figure(figsize=(10, 6))
    sns.histplot(df['selmer_rank'].dropna(), bins=range(int(df['selmer_rank'].max()) + 2))
    plt.xlabel('Elliptic Curve Rank')
    plt.ylabel('Count')
    plt.title('Anthropic Principle: Rank Distribution of Elliptic Curves')
    plt.savefig(f'{output_prefix}_anthropic_test.png')
    plt.close()
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    def animate(i):
        ax.clear()
        subset = df.iloc[:i*1000+1000]
        sns.histplot(subset['selmer_rank'].dropna(), bins=range(int(subset['selmer_rank'].max()) + 2), ax=ax)
        ax.set_xlabel('Elliptic Curve Rank')
        ax.set_ylabel('Count')
        ax.set_title('Rank Distribution Evolution')
    anim = animation.FuncAnimation(fig, animate, frames=50, interval=100, blit=False)
    anim.save(f'{output_prefix}_anthropic_animation.mp4', writer='ffmpeg', fps=30)
    plt.close()
    analysis_logger.info(f"anthropic_principle_test: {summary}", extra={'summary': str(summary)})
    return summary

def visualize_3d_manifold(df, coords_cols=['ra', 'dec', 'z'], weight_col='entropy', color_col='selmer_rank'):
    if gudhi is None:
        logging.warning("visualize_3d_manifold: gudhi not installed. Skipping manifold video.")
        return {'Status': 'gudhi not installed'}
    X_coords = df[coords_cols + [weight_col, color_col]].dropna()
    summary = {'Valid Rows': len(X_coords)}
    if X_coords.empty:
        logging.warning("visualize_3d_manifold: No valid coordinates for manifold visualization")
        summary['Status'] = 'No valid coordinates'
        return summary
    if len(X_coords) > MAX_COHOM_POINTS:
        X_coords = X_coords.sample(MAX_COHOM_POINTS, random_state=42)
        summary['Subsampled Rows'] = MAX_COHOM_POINTS
        logging.info(f"Subsampled to {MAX_COHOM_POINTS} points for manifold visualization")
    points = X_coords[coords_cols].values
    scaler = StandardScaler()
    points = scaler.fit_transform(points)
    weights = X_coords[weight_col].values
    weights = np.where(np.isfinite(weights), weights, np.median(weights[np.isfinite(weights)]))
    colors = X_coords[color_col]
    dist = cdist(points, points)
    max_filtration = np.max(dist) if np.isfinite(dist).any() else 1.0
    w_rips = WeightedRipsComplex(distance_matrix=dist, weights=weights, max_filtration=max_filtration)
    simplex_tree = w_rips.create_simplex_tree(max_dimension=2)
    simplices = []
    for simplex, _ in simplex_tree.get_simplices():
        simplices.append(simplex)
    if not simplices:
        logging.warning("visualize_3d_manifold: No simplices found. Falling back to scatter plot.")
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(points[:, 0], points[:, 1], points[:, 2], c=colors, s=50, alpha=0.6, cmap='viridis')
        ax.set_xlabel('RA (scaled)')
        ax.set_ylabel('Dec (scaled)')
        ax.set_zlabel('z (scaled)')
        ax.set_title('3D Galaxy Scatter (No Manifold)')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_3d_manifold_fallback.png')
        plt.close()
        summary['Status'] = 'Fallback to scatter'
        summary['Output File'] = f'{OUTPUT_PLOT_PREFIX}_3d_manifold_fallback.png'
        return summary
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    def update_frame(i):
        ax.clear()
        ax.set_xlabel('RA (scaled)')
        ax.set_ylabel('Dec (scaled)')
        ax.set_zlabel('z (scaled)')
        ax.set_title(f'3D Manifold Construction (Simplex {i+1}/{len(simplices)})')
        for j in range(min(i + 1, len(simplices))):
            simplex = simplices[j]
            if len(simplex) == 1:
                idx = simplex[0]
                ax.scatter(points[idx, 0], points[idx, 1], points[idx, 2], c=[colors.iloc[idx]], s=50, alpha=0.6, cmap='viridis')
            elif len(simplex) == 2:
                idx1, idx2 = simplex
                x = [points[idx1, 0], points[idx2, 0]]
                y = [points[idx1, 1], points[idx2, 1]]
                z = [points[idx1, 2], points[idx2, 2]]
                ax.plot(x, y, z, c='black', alpha=0.3)
            elif len(simplex) == 3:
                idx1, idx2, idx3 = simplex
                x = [points[idx1, 0], points[idx2, 0], points[idx3, 0], points[idx1, 0]]
                y = [points[idx1, 1], points[idx2, 1], points[idx3, 1], points[idx1, 1]]
                z = [points[idx1, 2], points[idx2, 2], points[idx3, 2], points[idx1, 2]]
                ax.plot(x, y, z, c='blue', alpha=0.2)
        ax.view_init(elev=20, azim=i * 2)
    anim = animation.FuncAnimation(fig, update_frame, frames=len(simplices), interval=100)
    output_file = f'{OUTPUT_PLOT_PREFIX}_3d_manifold.mp4'
    anim.save(output_file, writer='ffmpeg', fps=30)
    plt.close()
    summary['Manifold Video'] = output_file
    analysis_logger.info(f"visualize_3d_manifold: Saved manifold video to {output_file}", extra={'summary': str(summary)})
    return summary

def interactive_visualization(df, feature_cols):
    print_step(18, "Interactive Visualization")
    available_cols = [col for col in feature_cols if col in df.columns]
    chart = alt.Chart(df).mark_circle().encode(
        x=alt.X('selmer_rank:Q', title='Rank'),
        y=alt.Y('betti_1:Q', title='Betti Number (H1)'),
        color=alt.Color('selmer_rank:Q', title='Rank', scale=alt.Scale(scheme='viridis')),
        size=alt.Size('logmass:Q', title='Logmass'),
        tooltip=['objid', 'logmass', 'petrorad_r', 'selmer_rank', 'selmer_status', 'entropy', 'betti_1']
    ).interactive().properties(
        width=800, height=400, title='Rank vs. Cohomology (Betti_1) by Rank and Logmass'
    )
    chart.save(f'{OUTPUT_PLOT_PREFIX}_interactive_scatter_cohomology.html')
    fig = px.scatter_3d(
        df, x='logmass', y='entropy', z='betti_1',
        color='selmer_rank', size='logmass',
        hover_data=['objid', 'selmer_rank', 'selmer_status', 'entropy', 'betti_1'],
        title='3D Galaxy Features with Cohomology and Rank'
    )
    fig.write_html(f'{OUTPUT_PLOT_PREFIX}_3d_scatter_cohomology.html')
    if gudhi is not None:
        X_coords = df[['ra', 'dec', 'z', 'entropy']].dropna()
        if not X_coords.empty:
            if len(X_coords) > MAX_COHOM_POINTS:
                X_coords = X_coords.sample(MAX_COHOM_POINTS, random_state=42)
            points = X_coords[['ra', 'dec', 'z']].values
            scaler = StandardScaler()
            points = scaler.fit_transform(points)
            dist = cdist(points, points)
            weights = X_coords['entropy'].values
            weights = np.where(np.isfinite(weights), weights, np.median(weights[np.isfinite(weights)]))
            w_rips = WeightedRipsComplex(distance_matrix=dist, weights=weights)
            simplex_tree = w_rips.create_simplex_tree(max_dimension=2)
            persistence = simplex_tree.persistence()
            plot_persistence_diagram(persistence)
            plt.title('Persistence Diagram for Galaxy Coordinates (Entropy-Weighted)')
            plt.savefig(f'{OUTPUT_PLOT_PREFIX}_persistence_diagram.png')
            plt.close()
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='entropy_gradient', y='betti_1', hue='selmer_rank', size='logmass', palette='viridis')
    plt.title('Entropy Gradient vs. Betti_1 by Rank')
    plt.savefig(f'{OUTPUT_PLOT_PREFIX}_entropy_gradient_betti1.png')
    plt.close()
    X_valid = df[available_cols].dropna()
    if not X_valid.empty:
        tsne = TSNE(n_components=2, random_state=42, n_jobs=-1)
        X_tsne = tsne.fit_transform(X_valid)
        df_tsne = pd.DataFrame(X_tsne, columns=['TSNE1', 'TSNE2'], index=X_valid.index)
        df_tsne['selmer_rank'] = df.loc[X_valid.index, 'selmer_rank']
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df_tsne, x='TSNE1', y='TSNE2', hue='selmer_rank', palette='viridis')
        plt.title('t-SNE of Galaxy Features with Cohomology and Rank')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_tsne_scatter_cohomology.png')
        plt.close()
    if not df.empty:
        fig, ax = plt.subplots()
        def animate(i):
            ax.clear()
            bin_df = df[(df['logmass'] > i) & (df['logmass'] <= i+1)]
            sns.scatterplot(data=bin_df, x='entropy_gradient', y='betti_1', hue='selmer_rank', ax=ax, palette='viridis')
            ax.set_title(f'Entropy Gradient vs Betti_1 (logmass bin {i}-{i+1})')
        anim = animation.FuncAnimation(fig, animate, frames=range(8, 13), interval=500)
        anim.save(f'{OUTPUT_PLOT_PREFIX}_entropy_gradient_video.mp4', writer='ffmpeg')
        plt.close()
    manifold_summary = visualize_3d_manifold(df)
    summary = {'Plots Generated': [
        'interactive_scatter_cohomology.html',
        '3d_scatter_cohomology.html',
        'entropy_gradient_betti1.png',
        'tsne_scatter_cohomology.png',
        'entropy_gradient_video.mp4'
    ]}
    if gudhi is not None:
        summary['Plots Generated'].append('persistence_diagram.png')
        summary['Plots Generated'].append(manifold_summary.get('Manifold Video', ''))
    summary['High_Rank_Plot'] = f'{OUTPUT_PLOT_PREFIX}_high_rank_scatter.png'
    high_rank_df = df[df['selmer_rank'] >= 3]
    if not high_rank_df.empty:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=high_rank_df, x='logmass', y='selmer_rank', hue='selmer_rank', size='logmass', palette='viridis')
        plt.title('High-Rank Curves (Rank >= 3) by Logmass')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_high_rank_scatter.png')
        plt.close()
    print_step(18, "Interactive Visualization", summary)
    return summary

def analyze_noise_points(df, feature_cols):
    available_cols = [col for col in feature_cols if col in df.columns]
    noise_df = df[df['structure_cluster'] == -1]
    clustered_df = df[df['structure_cluster'] != -1]
    noise_stats = noise_df[available_cols].describe()
    clustered_stats = clustered_df[available_cols].describe()
    noise_nan_prop = noise_df[available_cols].isna().mean()
    clustered_nan_prop = clustered_df[available_cols].isna().mean()
    noise_structure_dist = noise_df['generator_structure'].apply(lambda x: x['structure'] if isinstance(x, dict) else 'unknown').value_counts()
    clustered_structure_dist = clustered_df['generator_structure'].apply(lambda x: x['structure'] if isinstance(x, dict) else 'unknown').value_counts()
    selmer_status_dist = df['selmer_status'].value_counts()
    noise_stats.to_csv(f'{OUTPUT_PLOT_PREFIX}_noise_vs_clustered_stats.csv')
    noise_nan_prop.to_csv(f'{OUTPUT_PLOT_PREFIX}_noise_nan_proportion.csv')
    clustered_nan_prop.to_csv(f'{OUTPUT_PLOT_PREFIX}_clustered_nan_proportion.csv')
    noise_structure_dist.to_csv(f'{OUTPUT_PLOT_PREFIX}_noise_structure_distribution.csv')
    clustered_structure_dist.to_csv(f'{OUTPUT_PLOT_PREFIX}_clustered_structure_distribution.csv')
    selmer_status_dist.to_csv(f'{OUTPUT_PLOT_PREFIX}_selmer_status_distribution.csv')
    summary = {
        'Noise Points': len(noise_df),
        'Clustered Points': len(clustered_df),
        'High_Rank_Noise': len(noise_df[noise_df['selmer_rank'] >= 3]),
        'High_Rank_Clustered': len(clustered_df[clustered_df['selmer_rank'] >= 3])
    }
    analysis_logger.info("Noise Points Statistics:\n" + str(noise_stats), extra={'summary': str(noise_stats)})
    analysis_logger.info("Clustered Points Statistics:\n" + str(clustered_stats), extra={'summary': str(clustered_stats)})
    analysis_logger.info("Noise Points NaN Proportion:\n" + str(noise_nan_prop), extra={'summary': str(noise_nan_prop)})
    analysis_logger.info("Clustered Points NaN Proportion:\n" + str(clustered_nan_prop), extra={'summary': str(clustered_nan_prop)})
    analysis_logger.info("Noise Points Structure Distribution:\n" + str(noise_structure_dist), extra={'summary': str(noise_structure_dist)})
    analysis_logger.info("Clustered Points Structure Distribution:\n" + str(clustered_structure_dist), extra={'summary': str(clustered_structure_dist)})
    analysis_logger.info("Selmer Status Distribution:\n" + str(selmer_status_dist), extra={'summary': str(selmer_status_dist)})
    return summary

def process_chunk(chunk, chunk_idx, total_chunks):
    print_step(20, f"process_chunk (Chunk {chunk_idx+1}/{total_chunks})")
    pari = cypari2.Pari()
    chunk = chunk.copy()
    chunk, impute_summary = impute_input_features(chunk)
    chunk['ra'] = chunk['ra'].where(chunk['ra'].notna(), -1)
    chunk['dec'] = chunk['dec'].where(chunk['dec'].notna(), -1)
    if chunk_idx < 3:  # Log z stats for first 3 chunks only
        logging.debug(f"process_chunk: z values in chunk {chunk_idx+1}: {chunk['z'].describe()}")
        invalid_z = chunk['z'][~chunk['z'].notna() | (chunk['z'] <= 0)]
        if not invalid_z.empty:
            logging.debug(f"process_chunk: Invalid z values: {invalid_z}")
    distance_results = chunk['z'].apply(calculate_distance_mpc)
    chunk['distance_mpc'] = distance_results.apply(lambda x: x[0])
    distance_summary = distance_results.apply(lambda x: x[1]).tolist()
    chunk['stellar_mass'] = chunk['logmass'].apply(convert_logmass_to_sm)
    chunk['radius_ly'] = chunk.apply(lambda x: estimate_radius_ly(x['petrorad_r'], x['distance_mpc']), axis=1)
    args_list = [(row['logmass'] * 1e6 if np.isfinite(row['logmass']) else np.nan,
                  (row['logmass'] * 1e6)**2 if np.isfinite(row['logmass']) else np.nan,
                  row['logmass'],
                  row.get('entropy', np.nan),
                  row.get('betti_1', np.nan),
                  row.get('entropy_gradient', np.nan),
                  pari) for _, row in chunk.iterrows()]
    try:
        parallel_results = list(compute_3selmer_rank([(args,) for args in args_list]))
        selmer_results = []
        error_counts = {'singular_curve': 0, 'two_descent_bool': 0, 'other_errors': 0}
        for (input_args, result) in parallel_results:
            if isinstance(result, tuple) and len(result) == 6:
                selmer_results.append(result)
                status = result[1]
                if status == 'singular_curve':
                    error_counts['singular_curve'] += 1
                elif status.startswith('invalid_output_bool'):
                    error_counts['two_descent_bool'] += 1
                elif status.startswith('error_'):
                    error_counts['other_errors'] += 1
            else:
                selmer_results.append((np.nan, 'parallel_error', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'parallel_error', 'Evidence': {}}))
                error_counts['other_errors'] += 1
                logging.warning(f"process_chunk: Invalid parallel result for args: {input_args[0]}")
        logging.info(f"process_chunk {chunk_idx+1}: Error summary - {error_counts}")
    except Exception as e:
        logging.error(f"process_chunk: Parallel computation failed - {str(e)}")
        selmer_results = []
        error_counts = {'singular_curve': 0, 'two_descent_bool': 0, 'other_errors': 0}
        for args in args_list:
            try:
                result = compute_3selmer_rank(args)
                if isinstance(result, tuple) and len(result) == 6:
                    selmer_results.append(result)
                    status = result[1]
                    if status == 'singular_curve':
                        error_counts['singular_curve'] += 1
                    elif status.startswith('invalid_output_bool'):
                        error_counts['two_descent_bool'] += 1
                    elif status.startswith('error_'):
                        error_counts['other_errors'] += 1
                else:
                    selmer_results.append((np.nan, 'parallel_error', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'parallel_error', 'Evidence': {}}))
                    error_counts['other_errors'] += 1
                    logging.warning(f"process_chunk: Invalid sequential result for args: {args}")
            except Exception as sub_e:
                selmer_results.append((np.nan, f'error_{str(sub_e)}', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': f'error_{str(sub_e)}', 'Evidence': {}}))
                error_counts['other_errors'] += 1
                logging.error(f"process_chunk: Sequential computation failed for args {args} - {str(sub_e)}")
        logging.info(f"process_chunk {chunk_idx+1}: Error summary - {error_counts}")
    chunk[['selmer_rank', 'selmer_status', 'torsion', 'j_invariant', 'discriminant']] = pd.DataFrame(
        [(r[0], r[1], r[2], r[3], r[4]) for r in selmer_results], index=chunk.index)
    mapping_summaries = [r[5] for r in selmer_results]
    chunk[['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion',
           'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap',
           'sato_tate', 'isogeny_count', 'log_min_isogeny', 'log_torsion_type']] = chunk.apply(
        lambda x: compute_mappings(x, pari)[0][['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion',
                                               'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap',
                                               'sato_tate', 'isogeny_count', 'log_min_isogeny', 'log_torsion_type']], axis=1)
    chunk['generator_coords'] = chunk['log_delta'].apply(lambda x: (x, x*2) if not pd.isna(x) else np.nan)
    chunk[['generator_structure', 'structure_summary']] = chunk['generator_coords'].apply(analyze_generator_structure).apply(pd.Series)
    high_rank_chunk = chunk[chunk['selmer_rank'] >= 3]
    if not high_rank_chunk.empty:
        high_rank_chunk.to_csv(f'{OUTPUT_PLOT_PREFIX}_high_rank_chunk_{chunk_idx+1}.csv', index=False)
    summary = {
        'Rows Processed': len(chunk),
        'NaN Counts': chunk[['logmass', 'petrorad_r', 'metallicity']].isna().sum().to_dict(),
        'Distance Summaries': distance_summary,
        'High_Rank_Curves': len(high_rank_chunk),
        'Error_Summary': error_counts
    }
    summary.update(impute_summary)
    print_step(20, f"process_chunk (Chunk {chunk_idx+1}/{total_chunks})", summary)
    return chunk

def process_cohomology(chunk, chunk_idx, total_chunks):
    print_step(21, f"process_cohomology (Chunk {chunk_idx+1}/{total_chunks})")
    chunk, betti_1, summary = compute_cohomology(chunk)
    print_step(21, f"process_cohomology (Chunk {chunk_idx+1}/{total_chunks})", summary)
    return chunk, betti_1

def main():
    print("               -- Initiating Program --")
    print_step(1, "Configuration")
    print_step(2, "Imports")
    print_step(22, "Main Processing")
    df = pd.read_csv(INPUT_FILE)
    df = df[REQUIRED_COLUMNS].iloc[:ROW_LIMIT]
    df[['logmass', 'metallicity']] = df[['logmass', 'metallicity']].replace(-9999, np.nan)
    summary = {'Initial Rows': len(df), 'NaN Counts': df[['logmass', 'metallicity']].isna().sum().to_dict()}
    print_step(22, "Data Loading", summary)

    print_step(20, "Chunk Processing")
    chunks = [df[i:i+CHUNKSIZE] for i in range(0, len(df), CHUNKSIZE)]
    total_chunks = len(chunks)
    with mp.Pool(processes=4) as pool:
        df_list = list(tqdm(pool.starmap(process_chunk, [(chunk, idx, total_chunks) for idx, chunk in enumerate(chunks)]), total=total_chunks, desc="Processing Chunks"))
    df = pd.concat(df_list, ignore_index=True)
    gc.collect()
    summary = {'Total Rows Processed': len(df), 'Chunks Processed': total_chunks}
    print_step(20, "Chunk Processing", summary)

    print_step(21, "Cohomology Processing")
    chunks = [df[i:i+CHUNKSIZE] for i in range(0, len(df), CHUNKSIZE)]
    with mp.Pool(processes=4) as pool:
        results = list(tqdm(pool.starmap(process_cohomology, [(chunk, idx, total_chunks) for idx, chunk in enumerate(chunks)]), total=total_chunks, desc="Cohomology Processing"))
    df_list = [res[0] for res in results]
    betti_1_vals = [res[1] for res in results]
    df = pd.concat(df_list, ignore_index=True)
    gc.collect()
    summary = {'Total Rows Processed': len(df), 'Betti_1 Values': betti_1_vals}
    print_step(21, "Cohomology Processing", summary)

    print_step(7, "Entropy Gradient Calculation")
    df, entropy_gradient, summary = compute_entropy_gradient(df)
    print_step(7, "Entropy Gradient Calculation", summary)

    print_step(9, "KDE Features Calculation")
    df, log_dens, summary = compute_kde_features(df, 'selmer_rank', 'var_ap')
    print_step(9, "KDE Features Calculation", summary)

    feature_cols = ['logmass', 'metallicity', 'petrorad_r', 'reg_cosmo', 't_cosmo', 'log_delta', 'log_omega',
                    'log_torsion', 'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap', 'sato_tate',
                    'isogeny_count', 'log_min_isogeny', 'log_torsion_type', 'selmer_rank',
                    'torsion', 'j_invariant', 'discriminant', 'entropy', 'betti_1', 'entropy_gradient']
    if 'kde_selmer_rank_var_ap' in df.columns:
        feature_cols.append('kde_selmer_rank_var_ap')

    print_step(22, "Check NaN Counts")
    available_cols = [col for col in feature_cols if col in df.columns]
    nan_counts = df[available_cols].isna().sum().to_dict()
    analysis_logger.info("NaN Counts in Features:\n" + str(nan_counts), extra={'summary': str(nan_counts)})
    pd.Series(nan_counts).to_csv(f'{OUTPUT_PLOT_PREFIX}_nan_counts.csv')
    summary = {'NaN Counts': {k: v for k, v in nan_counts.items() if v > 0}}
    print_step(22, "Check NaN Counts", summary)

    print_step(5, "Impute Derived Features")
    df = impute_derived_features(df, feature_cols)
    summary = {'Rows Processed': len(df)}
    print_step(5, "Impute Derived Features", summary)

    print_step(22, "Statistical Mechanics Test")
    stat_mech_summary = statistical_mechanics_test(df)
    print_step(22, "Statistical Mechanics Test", stat_mech_summary)

    print_step(22, "Tully-Fisher Test")
    tully_fisher_summary = tully_fisher_test(df, available_cols)
    print_step(22, "Tully-Fisher Test", tully_fisher_summary)

    print_step(22, "Math-Physics Unification Test")
    math_physics_summary = math_physics_unification_test(df)
    print_step(22, "Math-Physics Unification Test", math_physics_summary)

    print_step(22, "Anthropic Principle Test")
    anthropic_summary = anthropic_principle_test(df)
    print_step(22, "Anthropic Principle Test", anthropic_summary)

    print_step(16, "Train Stacking Classifier for High-Rank Curves")
    df['is_high_rank'] = (df['selmer_rank'] >= 3).astype(int)
    X = df[available_cols]
    y = df['is_high_rank']
    catboost_params_clf = optimize_catboost_classifier(X, y) if CatBoostClassifier and create_study else None
    classifiers = [
        ('RandomForest', RandomForestClassifier(random_state=42, n_jobs=-1)),
        ('HistGradientBoosting', HistGradientBoostingClassifier(random_state=42))
    ]
    if XGBClassifier:
        classifiers.append(('XGBoost', XGBClassifier(random_state=42, n_jobs=-1)))
    if LGBMClassifier:
        classifiers.append(('LightGBM', LGBMClassifier(random_state=42, n_jobs=-1)))
    if CatBoostClassifier and catboost_params_clf:
        classifiers.append(('CatBoost', CatBoostClassifier(**catboost_params_clf, verbose=0)))
    stacking_clf = StackingClassifier(estimators=classifiers, final_estimator=HistGradientBoostingClassifier(random_state=42), n_jobs=-1)
    stacking_clf.fit(X, y)
    gen_accuracy = cross_val_score(stacking_clf, X, y, cv=5, n_jobs=-1).mean()
    class_report = classification_report(y, stacking_clf.predict(X), output_dict=True)
    analysis_logger.info("Stacking Classifier Accuracy for High-Rank Curves:" + str(gen_accuracy), extra={'summary': str(gen_accuracy)})
    analysis_logger.info("Classification Report for High-Rank Curves:\n" + str(class_report), extra={'summary': str(class_report)})
    summary = {'Accuracy': gen_accuracy, 'Classification Report': class_report}
    print_step(16, "Train Stacking Classifier for High-Rank Curves", summary)

    print_step(16, "Compute Feature Importance for High-Rank Curves")
    gen_perm_importance = permutation_importance(stacking_clf, X, y, n_repeats=10, random_state=42, n_jobs=-1)
    gen_feature_importance = pd.Series(gen_perm_importance.importances_mean, index=X.columns).sort_values(ascending=False)
    analysis_logger.info("High-Rank Curve Feature Importance:\n" + str(gen_feature_importance), extra={'summary': str(gen_feature_importance)})
    gen_feature_importance.to_csv(f'{OUTPUT_PLOT_PREFIX}_high_rank_feature_importance.csv')
    summary = {'Top Features': gen_feature_importance.head(5).to_dict()}
    print_step(16, "Compute Feature Importance for High-Rank Curves", summary)

    plt.figure(figsize=(10, 6))
    sns.barplot(x=gen_feature_importance.values, y=gen_feature_importance.index)
    plt.title('High-Rank Curve Feature Importance')
    plt.savefig(f'{OUTPUT_PLOT_PREFIX}_high_rank_feature_importance.png')
    plt.close()

    print_step(17, "Clustering Analysis")
    X_struct = preprocess_clustering_features(df, feature_cols)
    dbscan = DBSCAN(eps=0.5, min_samples=5, n_jobs=-1)
    cluster_labels = dbscan.fit_predict(X_struct[available_cols])
    df['structure_cluster'] = cluster_labels
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = sum(cluster_labels == -1)
    summary = {
        'Number of Clusters': n_clusters,
        'Number of Noise Points': n_noise
    }
    print_step(17, "Clustering Analysis", summary)

    print_step(17, "Analyze Noise Points")
    noise_summary = analyze_noise_points(df, feature_cols)
    print_step(17, "Analyze Noise Points", noise_summary)

    print_step(18, "Interactive Visualization")
    interactive_summary = interactive_visualization(df, feature_cols)
    print_step(18, "Interactive Visualization", interactive_summary)

    print("               -- Program Complete --")
    print(f"Final DataFrame shape: {df.shape}")
    df.to_csv(f'{OUTPUT_PLOT_PREFIX}_final_dataframe.csv', index=False)
    print(f"Saved final DataFrame to {OUTPUT_PLOT_PREFIX}_final_dataframe.csv")

if __name__ == "__main__":
    main()
