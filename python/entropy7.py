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

# Configuration
INPUT_FILE = 'GalSpecExtra.csv'
OUTPUT_PLOT_PREFIX = 'final_two_tier_synthesis_v48'
CHUNKSIZE = 25000
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

# Logging setup
import logging
import csv
logging.basicConfig(filename='debug.log', level=logging.DEBUG)
analysis_logger = logging.getLogger('analysis')
analysis_handler = logging.FileHandler('analysis.log')
analysis_logger.addHandler(analysis_handler)
analysis_logger.setLevel(logging.INFO)

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

def print_step(step_num, step_name, summary=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[STEP {step_num}] {timestamp} - {step_name}")
    logging.info(f"Step {step_num}: {step_name}")
    if summary is not None:
        print(f"[SUMMARY {step_num}] {step_name} completed.")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        analysis_logger.info(f"Step {step_num} Summary: {summary}", extra={'summary': str(summary)})

def impute_input_features(chunk, impute_cols=['ra', 'dec', 'z', 'metallicity'], target_cols=['logmass', 'petrorad_r']):
    chunk = chunk.copy()
    logging.debug(f"impute_input_features: Invalid z values before clipping: {chunk['z'][~chunk['z'].notna() | (chunk['z'] <= 0)]}")
    imputer = KNNImputer(n_neighbors=10, weights='distance')
    X = chunk[impute_cols + target_cols]
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=impute_cols + target_cols, index=chunk.index)
    for target in target_cols + ['metallicity']:
        nan_idx = chunk[target].isna()
        if nan_idx.any():
            chunk.loc[nan_idx, target] = X_imputed.loc[nan_idx, target]
            logging.debug(f"impute_input_features: Imputed {target} for {nan_idx.sum()} rows")
    chunk['z'] = np.clip(chunk['z'], 1e-6, None)
    chunk['metallicity'] = np.clip(np.abs(chunk['metallicity']) + 1e-6, 1e-6, None)
    summary = {
        'Imputed logmass': np.int64(chunk['logmass'].isna().sum()),
        'Imputed petrorad_r': np.int64(chunk['petrorad_r'].isna().sum()),
        'Imputed metallicity': np.int64(chunk['metallicity'].isna().sum()),
        'z_min': chunk['z'].min(),
        'metallicity_min': chunk['metallicity'].min()
    }
    logging.debug(f"impute_input_features: {summary}")
    return chunk, summary

def impute_derived_features(df, feature_cols):
    df = df.copy()
    imputer = KNNImputer(n_neighbors=5, weights='distance')
    available_cols = [col for col in feature_cols if col in df.columns]
    X = df[available_cols]
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=available_cols, index=df.index)
    for col in available_cols:
        nan_idx = df[col].isna()
        if nan_idx.any():
            df.loc[nan_idx, col] = X_imputed.loc[nan_idx, col]
            logging.debug(f"impute_derived_features: Imputed {col} for {nan_idx.sum()} rows")
    return df

def estimate_entropy(row, median_entropy=0):
    try:
        z = row['z']
        if not np.isfinite(z) or z <= 0:
            logging.debug(f"estimate_entropy: Invalid z={z}, using median entropy")
            return median_entropy, {'Entropy': median_entropy, 'Status': 'Invalid z'}
        T_proxy = cosmo.Tcmb(z).value
        rho_proxy = max(1e-6, abs(row['metallicity']) * 1e-3)
        S = KB * np.log(T_proxy / (rho_proxy ** (2/3)))
        summary = {'Entropy': S, 'Status': 'Computed'}
        if not np.isfinite(S):
            logging.debug(f"estimate_entropy: Non-finite entropy={S}, using median")
            summary = {'Entropy': median_entropy, 'Status': 'Fallback to median'}
            return median_entropy, summary
        return S, summary
    except Exception as e:
        logging.debug(f"estimate_entropy: Error - {str(e)}")
        return median_entropy, {'Entropy': median_entropy, 'Status': f'Error: {str(e)}'}

def compute_entropy_gradient(df, entropy_col='entropy', feature_cols=['logmass', 'petrorad_r']):
    df = df.copy()
    X_valid = df[[entropy_col] + feature_cols].dropna()
    summary = {'Valid Rows': len(X_valid)}
    if X_valid.empty:
        logging.warning("compute_entropy_gradient: No valid data for gradient")
        return df, np.zeros(len(df)), summary
    grad = np.zeros(len(df))
    for feat in feature_cols:
        grad_valid = np.gradient(X_valid[entropy_col], X_valid[feat])
        grad[X_valid.index] += grad_valid
    df['entropy_gradient'] = grad
    df['entropy_gradient'] = df['entropy_gradient'].fillna(0)
    summary['Gradient Mean'] = np.mean(grad) if np.isfinite(grad).any() else np.nan
    analysis_logger.info(f"compute_entropy_gradient: Computed entropy gradient", extra={'summary': str(summary)})
    return df, grad, summary

def compute_cohomology(df, coords_cols=['ra', 'dec', 'z'], entropy_col='entropy', max_dimension=2):
    if gudhi is None:
        logging.warning("compute_cohomology: gudhi not installed. Returning NaN for betti_1")
        summary = {'Status': 'gudhi not installed', 'Betti_1': 'NaN'}
        return df, np.full(len(df), np.nan), summary
    X_coords = df[coords_cols + [entropy_col]].dropna()
    summary = {'Valid Rows': len(X_coords)}
    if X_coords.empty:
        logging.warning("compute_cohomology: No valid coordinates for homology")
        summary['Status'] = 'No valid coordinates'
        return df, np.full(len(df), np.nan), summary
    if len(X_coords) > MAX_COHOM_POINTS:
        X_coords = X_coords.sample(MAX_COHOM_POINTS, random_state=42)
        summary['Subsampled Rows'] = MAX_COHOM_POINTS
        logging.info(f"Subsampled to {MAX_COHOM_POINTS} points for cohomology")
    points = X_coords[coords_cols].values
    scaler = StandardScaler()
    points = scaler.fit_transform(points)
    weights = X_coords[entropy_col].values
    weights = np.where(np.isfinite(weights), weights, np.median(weights[np.isfinite(weights)]))
    dist = cdist(points, points)
    max_filtration = np.max(dist) if np.isfinite(dist).any() else 1.0
    w_rips = WeightedRipsComplex(distance_matrix=dist, weights=weights, max_filtration=max_filtration)
    simplex_tree = w_rips.create_simplex_tree(max_dimension=max_dimension + 1)
    persistence = simplex_tree.persistence()
    betti_numbers = simplex_tree.betti_numbers()
    betti_1 = betti_numbers[1] if len(betti_numbers) > 1 else 0
    df['betti_1'] = np.nan
    df.loc[X_coords.index, 'betti_1'] = betti_1
    summary['Betti_1'] = betti_1
    analysis_logger.info(f"compute_cohomology: Betti_1 = {betti_1}", extra={'summary': str(summary)})
    return df, betti_1, summary

def compute_kde_features(df, rank_col='selmer_rank', lfunc_col='var_ap'):
    X_kde = df[[rank_col, lfunc_col]].dropna()
    summary = {'Valid Rows': len(X_kde)}
    if X_kde.empty:
        logging.warning("compute_kde_features: No valid data for KDE")
        summary['Status'] = 'No valid data'
        return df, np.zeros(len(df)), summary
    kde = KernelDensity(kernel='gaussian', bandwidth=0.5).fit(X_kde)
    log_dens = kde.score_samples(X_kde)
    df_kde = pd.DataFrame({f'kde_{rank_col}_{lfunc_col}': log_dens}, index=X_kde.index)
    df = df.join(df_kde)
    df[f'kde_{rank_col}_{lfunc_col}'] = df[f'kde_{rank_col}_{lfunc_col}'].fillna(0)
    summary['KDE Density Mean'] = np.mean(log_dens) if np.isfinite(log_dens).any() else np.nan
    analysis_logger.info(f"compute_kde_features: Added KDE density for {rank_col} and {lfunc_col}", extra={'summary': str(summary)})
    return df, log_dens, summary

def calculate_distance_mpc(z):
    if z is None or not np.isfinite(z) or z <= 0:
        return np.nan, {'Distance': np.nan, 'Status': 'Invalid input'}
    try:
        distance = float(cosmo.comoving_distance(z).to(u.Mpc).value)
        return distance, {'Distance': distance, 'Status': 'Computed'}
    except Exception as e:
        logging.debug(f"calculate_distance_mpc: Error - {str(e)}")
        return np.nan, {'Distance': np.nan, 'Status': f'Error: {str(e)}'}

def convert_logmass_to_sm(logmass):
    if not np.isfinite(logmass):
        return np.nan
    return 10**logmass

def estimate_radius_ly(angular_size_arcsec, distance_mpc):
    if not (np.isfinite(angular_size_arcsec) and np.isfinite(distance_mpc) and angular_size_arcsec > 0 and distance_mpc > 0):
        return np.nan
    angle_rad = (angular_size_arcsec * u.arcsec).to(u.rad).value
    return angle_rad * distance_mpc * 3.262e6

@parallel(ncpus=6)
def compute_3selmer_rank(args):
    delta, conductor, logmass, entropy, betti_1, entropy_gradient, pari = args
    entropy = 0 if np.isnan(entropy) else entropy
    betti_1 = 0 if np.isnan(betti_1) else betti_1
    entropy_gradient = 0 if np.isnan(entropy_gradient) else entropy_gradient
    if not all(np.isfinite(x) for x in [delta, conductor, logmass]):
        logging.debug(f"compute_3selmer_rank: Skipped - Invalid delta={delta}, conductor={conductor}, logmass={logmass}")
        return np.nan, 'invalid_input', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'invalid_input', 'Evidence': {}}
    try:
        scale_factor = max(1e3, np.log10(max(1, abs(delta))))
        delta_scaled = int(delta / scale_factor)
        conductor_scaled = min(int(delta_scaled**2), MAX_CONDUCTOR)
        if conductor_scaled > MAX_CONDUCTOR:
            logging.debug(f"compute_3selmer_rank: Skipped - Scaled conductor={conductor_scaled} > MAX_CONDUCTOR")
            return np.nan, 'large_conductor', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'large_conductor', 'Evidence': {}}
        a = -delta_scaled
        b = delta_scaled**2 + entropy * logmass + COHOMOLOGY_WEIGHT * betti_1 + ENTROPY_GRADIENT_WEIGHT * entropy_gradient
        if not np.isfinite(a) or not np.isfinite(b):
            logging.debug(f"compute_3selmer_rank: Invalid curve parameters a={a}, b={b}")
            return np.nan, 'invalid_curve_params', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'invalid_curve_params', 'Evidence': {}}
        E = EllipticCurve(QQ, [0, 0, 0, a, b]).minimal_model()
        curve_name = f"a={a},b={b}"
        evidence = {}
        try:
            rank_standard = E.rank(only_use_mwrank=False)
            evidence['standard_rank'] = {'value': rank_standard, 'status': 'success'}
        except Exception as e:
            rank_standard = np.nan
            evidence['standard_rank'] = {'value': np.nan, 'status': f'error_{str(e)}'}
            logging.warning(f"compute_3selmer_rank: Standard rank failed for curve {curve_name} - {str(e)}")
        try:
            selmer_rank = E.selmer_rank()
            evidence['selmer_rank'] = {'value': selmer_rank, 'status': 'success'}
        except Exception as e:
            selmer_rank = np.nan
            evidence['selmer_rank'] = {'value': np.nan, 'status': f'error_{str(e)}'}
            logging.warning(f"compute_3selmer_rank: Selmer rank failed for curve {curve_name} - {str(e)}")
        try:
            pari.allocatemem(16000000)  # Increase PARI stack size
            two_desc = E.two_descent(second_limit=100, verbose=False)
            if isinstance(two_desc, tuple) and len(two_desc) >= 3 and all(isinstance(x, (int, float)) for x in two_desc[:2]):
                rank_lower, rank_upper, _ = two_desc[:3]
                evidence['two_descent'] = {
                    'lower_bound': rank_lower,
                    'upper_bound': rank_upper,
                    'status': 'success'
                }
            else:
                evidence['two_descent'] = {
                    'lower_bound': np.nan,
                    'upper_bound': np.nan,
                    'status': f'invalid_output_type_{type(two_desc).__name__}',
                    'expected': 'tuple with at least 3 elements (lower_bound, upper_bound, ...)',
                    'received': str(two_desc)
                }
                logging.warning(f"compute_3selmer_rank: two_descent returned invalid output for curve {curve_name}: {two_desc}. Expected tuple with rank bounds.")
                rank_lower = np.nan
                rank_upper = np.nan
        except Exception as e:
            evidence['two_descent'] = {
                'lower_bound': np.nan,
                'upper_bound': np.nan,
                'status': f'error_{str(e)}',
                'expected': 'tuple with at least 3 elements (lower_bound, upper_bound, ...)',
                'received': 'exception'
            }
            logging.warning(f"compute_3selmer_rank: two_descent failed for curve {curve_name} - {str(e)}. Expected tuple with rank bounds.")
            rank_lower = np.nan
            rank_upper = np.nan
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
            logging.warning(f"compute_3selmer_rank: Torsion/discriminant failed for curve {curve_name} - {str(e)}")
        valid_ranks = [r for r in [
            evidence.get('standard_rank', {}).get('value'),
            evidence.get('selmer_rank', {}).get('value'),
            evidence.get('two_descent', {}).get('lower_bound')
        ] if not np.isnan(r) and r is not None]
        if valid_ranks:
            final_rank = min(valid_ranks) if len(valid_ranks) == 1 else int(np.median(valid_ranks))
            status = 'success' if final_rank <= SELMER_BOUND else 'high_rank'
        else:
            final_rank = np.nan
            if 'selmer_rank' in evidence and not np.isnan(evidence['selmer_rank'].get('value')):
                final_rank = evidence['selmer_rank']['value']
                status = f'fallback_selmer_rank_{int(final_rank)}'
            else:
                status = 'no_valid_ranks'
                logging.info(f"compute_3selmer_rank: No valid ranks for curve {curve_name}. Falling back to NaN.")
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
            'Curve_Name': curve_name
        }
        analysis_logger.info(f"compute_3selmer_rank: {summary}", extra={'summary': str(summary)})
        if final_rank > SELMER_BOUND:
            logging.debug(f"compute_3selmer_rank: High rank={final_rank} > SELMER_BOUND={SELMER_BOUND} for curve {curve_name}")
        return np.nan, 'parallel_wrapper', np.nan, np.nan, np.nan, (final_rank, status, torsion, j_inv, disc, summary)
    except Exception as e:
        logging.error(f"compute_3selmer_rank: General error for curve {curve_name} - {str(e)}")
        return np.nan, f'error_{str(e)}', np.nan, np.nan, np.nan, {
            'Rank': 'NaN',
            'Status': f'error_{str(e)}',
            'Evidence': {},
            'Curve_Name': curve_name
        }

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

def classify_generator(row):
    if pd.isna(row['log_delta']):
        return 'unknown', 1.0, {'Generator_Type': 'unknown', 'Simplicity_Score': 1.0}
    simplicity_score = abs(row['log_delta'] - round(row['log_delta']))
    generator_type = 'Simple' if simplicity_score < 0.1 else 'Recursive'
    return generator_type, simplicity_score, {'Generator_Type': generator_type, 'Simplicity_Score': simplicity_score}

def analyze_generator_structure(coords):
    if pd.isna(coords):
        return {'type': 'unknown', 'structure': 'unknown'}, {'Type': 'unknown', 'Structure': 'unknown'}
    x, y = coords if isinstance(coords, tuple) else (np.nan, np.nan)
    if pd.isna(x) or pd.isna(y):
        return {'type': 'unknown', 'structure': 'unknown'}, {'Type': 'unknown', 'Structure': 'unknown'}
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and float(x).is_integer() and float(y).is_integer():
        return {'type': 'Simple', 'structure': 'integer'}, {'Type': 'Simple', 'Structure': 'integer'}
    denom_x = x.denominator() if hasattr(x, 'denominator') else 1
    denom_y = y.denominator() if hasattr(y, 'denominator') else 1
    factors_x = factor(denom_x) if denom_x != 1 else []
    if len(factors_x) == 1 and len(factors_x[0][0].prime_factors()) == 1:
        return {'type': 'Recursive', 'structure': 'power_of_prime'}, {'Type': 'Recursive', 'Structure': 'power_of_prime'}
    return {'type': 'Recursive', 'structure': 'other_sequence'}, {'Type': 'Recursive', 'Structure': 'other_sequence'}

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
        'Stability_Ratio': stability_ratio
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

def visualize_3d_manifold(df, coords_cols=['ra', 'dec', 'z'], weight_col='entropy', color_col='generator_type'):
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
    colors = X_coords[color_col].map({'Simple': 'blue', 'Recursive': 'red', 'unknown': 'gray'})
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
        ax.scatter(points[:, 0], points[:, 1], points[:, 2], c=colors, s=50, alpha=0.6)
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
                ax.scatter(points[idx, 0], points[idx, 1], points[idx, 2], c=colors.iloc[idx], s=50, alpha=0.6)
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
        color='generator_type:N',
        size=alt.Size('simplicity_score:Q', title='Simplicity Score'),
        tooltip=['objid', 'logmass', 'petrorad_r', 'selmer_rank', 'selmer_status', 'entropy', 'betti_1', 'simplicity_score']
    ).interactive().properties(
        width=800, height=400, title='Rank vs. Cohomology (Betti_1) by Generator Type and Simplicity Score'
    )
    chart.save(f'{OUTPUT_PLOT_PREFIX}_interactive_scatter_cohomology.html')
    fig = px.scatter_3d(
        df, x='logmass', y='entropy', z='betti_1',
        color='generator_type', size='simplicity_score',
        hover_data=['objid', 'selmer_rank', 'selmer_status', 'entropy', 'betti_1', 'simplicity_score'],
        title='3D Galaxy Features with Cohomology and Simplicity Score'
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
    sns.scatterplot(data=df, x='entropy_gradient', y='betti_1', hue='generator_type', size='simplicity_score')
    plt.title('Entropy Gradient vs. Betti_1 by Generator Type')
    plt.savefig(f'{OUTPUT_PLOT_PREFIX}_entropy_gradient_betti1.png')
    plt.close()
    X_valid = df[available_cols].dropna()
    if not X_valid.empty:
        tsne = TSNE(n_components=2, random_state=42, n_jobs=-1)
        X_tsne = tsne.fit_transform(X_valid)
        df_tsne = pd.DataFrame(X_tsne, columns=['TSNE1', 'TSNE2'], index=X_valid.index)
        df_tsne['generator_type'] = df.loc[X_valid.index, 'generator_type']
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df_tsne, x='TSNE1', y='TSNE2', hue='generator_type')
        plt.title('t-SNE of Galaxy Features with Cohomology and Simplicity Score')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_tsne_scatter_cohomology.png')
        plt.close()
    if not df.empty:
        fig, ax = plt.subplots()
        def animate(i):
            ax.clear()
            bin_df = df[(df['logmass'] > i) & (df['logmass'] <= i+1)]
            sns.scatterplot(data=bin_df, x='entropy_gradient', y='betti_1', ax=ax)
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
    print_step(18, "Interactive Visualization", summary)
    return summary

def analyze_noise_points(df, feature_cols):
    available_cols = [col for col in feature_cols if col in df.columns]
    recursive_df = df[df['generator_type'] == 'Recursive']
    noise_df = recursive_df[recursive_df['structure_cluster'] == -1]
    clustered_df = recursive_df[recursive_df['structure_cluster'] != -1]
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
        'Clustered Points': len(clustered_df)
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
    logging.debug(f"process_chunk: z values in chunk {chunk_idx+1}: {chunk['z'].describe()}")
    logging.debug(f"process_chunk: Invalid z values: {chunk['z'][~chunk['z'].notna() | (chunk['z'] <= 0)]}")
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
        for (input_args, result) in parallel_results:
            if isinstance(result, tuple) and len(result) == 6:
                selmer_results.append(result)
            else:
                selmer_results.append((np.nan, 'parallel_error', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'parallel_error', 'Evidence': {}}))
                logging.warning(f"process_chunk: Invalid parallel result for args: {input_args[0]}")
    except Exception as e:
        logging.error(f"process_chunk: Parallel computation failed - {str(e)}")
        selmer_results = []
        for args in args_list:
            try:
                result = compute_3selmer_rank(args)
                if isinstance(result, tuple) and len(result) == 6:
                    selmer_results.append(result)
                else:
                    selmer_results.append((np.nan, 'parallel_error', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': 'parallel_error', 'Evidence': {}}))
                    logging.warning(f"process_chunk: Invalid sequential result for args: {args}")
            except Exception as sub_e:
                selmer_results.append((np.nan, f'error_{str(sub_e)}', np.nan, np.nan, np.nan, {'Rank': 'NaN', 'Status': f'error_{str(sub_e)}', 'Evidence': {}}))
                logging.error(f"process_chunk: Sequential computation failed for args {args} - {str(sub_e)}")
    chunk[['selmer_rank', 'selmer_status', 'torsion', 'j_invariant', 'discriminant']] = pd.DataFrame(
        [(r[0], r[1], r[2], r[3], r[4]) for r in selmer_results], index=chunk.index)
    mapping_summaries = [r[5] for r in selmer_results]
    chunk[['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion',
           'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap',
           'sato_tate', 'isogeny_count', 'log_min_isogeny', 'log_torsion_type']] = chunk.apply(
        lambda x: compute_mappings(x, pari)[0][['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion',
                                               'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap',
                                               'sato_tate', 'isogeny_count', 'log_min_isogeny', 'log_torsion_type']], axis=1)
    chunk[['generator_type', 'simplicity_score', 'generator_summary']] = chunk.apply(classify_generator, axis=1, result_type='expand')
    chunk['generator_coords'] = chunk['log_delta'].apply(lambda x: (x, x*2) if not pd.isna(x) else np.nan)
    chunk[['generator_structure', 'structure_summary']] = chunk['generator_coords'].apply(analyze_generator_structure).apply(pd.Series)
    summary = {
        'Rows Processed': len(chunk),
        'NaN Counts': chunk[['logmass', 'petrorad_r', 'metallicity']].isna().sum().to_dict(),
        'Distance Summaries': distance_summary
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
    with mp.Pool(processes=6) as pool:
        df_list = list(tqdm(pool.starmap(process_chunk, [(chunk, idx, total_chunks) for idx, chunk in enumerate(chunks)]), total=total_chunks, desc="Processing Chunks"))
    df = pd.concat(df_list, ignore_index=True)
    gc.collect()
    summary = {'Total Rows Processed': len(df), 'Chunks Processed': total_chunks}
    print_step(20, "Chunk Processing", summary)

    print_step(21, "Cohomology Processing")
    chunks = [df[i:i+CHUNKSIZE] for i in range(0, len(df), CHUNKSIZE)]
    with mp.Pool(processes=6) as pool:
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

    print_step(22, "Check Class Distribution")
    class_dist = df['generator_type'].value_counts().to_dict()
    analysis_logger.info("Generator Type Distribution:\n" + str(class_dist), extra={'summary': str(class_dist)})
    summary = {'Generator Type Distribution': class_dist}
    print_step(22, "Check Class Distribution", summary)

    feature_cols = ['logmass', 'metallicity', 'petrorad_r', 'reg_cosmo', 't_cosmo', 'log_delta', 'log_omega',
                    'log_torsion', 'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap', 'sato_tate',
                    'isogeny_count', 'log_min_isogeny', 'log_torsion_type', 'simplicity_score', 'selmer_rank',
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

    print_step(16, "Train Stacking Classifier")
    X = df[available_cols]
    y = df['generator_type']
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
    analysis_logger.info("Stacking Classifier Accuracy:" + str(gen_accuracy), extra={'summary': str(gen_accuracy)})
    analysis_logger.info("Classification Report:\n" + str(class_report), extra={'summary': str(class_report)})
    summary = {'Accuracy': gen_accuracy}
    print_step(16, "Train Stacking Classifier", summary)

    print_step(16, "Compute Generator Feature Importance")
    gen_perm_importance = permutation_importance(stacking_clf, X, y, n_repeats=10, random_state=42, n_jobs=-1)
    gen_feature_importance = pd.Series(gen_perm_importance.importances_mean, index=X.columns).sort_values(ascending=False)
    analysis_logger.info("Generator Type Feature Importance:\n" + str(gen_feature_importance), extra={'summary': str(gen_feature_importance)})
    gen_feature_importance.to_csv(f'{OUTPUT_PLOT_PREFIX}_generator_feature_importance.csv')
    summary = {'Top Features': gen_feature_importance.head(5).to_dict()}
    print_step(16, "Compute Generator Feature Importance", summary)

    plt.figure(figsize=(10, 6))
    sns.barplot(x=gen_feature_importance.values, y=gen_feature_importance.index)
    plt.title('Generator Type Feature Importance')
    plt.savefig(f'{OUTPUT_PLOT_PREFIX}_generator_feature_importance.png')
    plt.close()

    print_step(17, "Symbolic Regression for Generator")
    for method in ['pysr', 'gplearn']:
        sym_reg_gen = run_symbolic_regression(X, y.map({'Simple': 0, 'Recursive': 1, 'unknown': 2}), feature_cols, method)
        if sym_reg_gen:
            getattr(sym_reg_gen, 'equations_', pd.DataFrame()).to_csv(f'{OUTPUT_PLOT_PREFIX}_symbolic_regression_generator_{method}.csv')
    summary = {'Methods Run': ['pysr', 'gplearn']}
    print_step(17, "Symbolic Regression for Generator", summary)

    print_step(15, "Perform Clustering")
    X_struct = df[df['generator_type'] == 'Recursive'][['logmass', 'metallicity', 'petrorad_r', 'log_delta', 'log_omega', 'entropy', 'betti_1', 'entropy_gradient'] +
                                                      (['kde_selmer_rank_var_ap'] if 'kde_selmer_rank_var_ap' in df.columns else [])]
    summary = {'Recursive Rows': len(X_struct)}
    if not X_struct.empty:
        X_struct = preprocess_clustering_features(X_struct, X_struct.columns)
        dbscan = DBSCAN(eps=0.5, min_samples=5, metric='nan_euclidean')
        cluster_labels = dbscan.fit_predict(X_struct)
        df.loc[df['generator_type'] == 'Recursive', 'structure_cluster'] = cluster_labels
        kmeans = KMeans(n_clusters=5, random_state=42, n_jobs=-1)
        kmeans_labels = kmeans.fit_predict(X_struct)
        df.loc[df['generator_type'] == 'Recursive', 'kmeans_cluster'] = kmeans_labels
        summary['DBSCAN Clusters'] = df[df['generator_type'] == 'Recursive']['structure_cluster'].value_counts().to_dict()
        summary['KMeans Clusters'] = df[df['generator_type'] == 'Recursive']['kmeans_cluster'].value_counts().to_dict()
        analysis_logger.info("Structure Clusters:" + str(summary['DBSCAN Clusters']), extra={'summary': str(summary['DBSCAN Clusters'])})
        analysis_logger.info("KMeans Clusters:" + str(summary['KMeans Clusters']), extra={'summary': str(summary['KMeans Clusters'])})
    print_step(15, "Perform Clustering", summary)

    print_step(19, "Analyze Noise Points")
    summary = analyze_noise_points(df, feature_cols)
    print_step(19, "Analyze Noise Points", summary)

    print_step(22, "Dimensionality Reduction")
    X_valid = df[available_cols].dropna()
    summary = {'Valid Rows': len(X_valid)}
    if not X_valid.empty:
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_valid)
        df_pca = pd.DataFrame(X_pca, columns=['PC1', 'PC2'], index=X_valid.index)
        df_pca['generator_type'] = df.loc[X_valid.index, 'generator_type']
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df_pca, x='PC1', y='PC2', hue='generator_type')
        plt.title('PCA of Galaxy Features with Cohomology and Simplicity Score')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_pca_scatter_cohomology.png')
        plt.close()
        summary['PCA Variance Ratio'] = pca.explained_variance_ratio_.tolist()
        analysis_logger.info(f"PCA Explained Variance Ratio: {summary['PCA Variance Ratio']}", extra={'summary': str(summary)})
    print_step(22, "Dimensionality Reduction", summary)

    print_step(18, "Interactive Visualization")
    vis_summary = interactive_visualization(df, feature_cols)
    print_step(18, "Interactive Visualization", vis_summary)

    print_step(23, "Saving Final Data")
    df.to_csv(f'{OUTPUT_PLOT_PREFIX}_processed_data.csv', index=False)
    summary = {'Output File': f'{OUTPUT_PLOT_PREFIX}_processed_data.csv', 'Rows Saved': len(df)}
    print_step(23, "Saving Final Data", summary)

    print_step(24, "Cleanup")
    gc.collect()
    plt.close('all')
    summary = {'Memory Freed': True}
    print_step(24, "Cleanup", summary)

    print("               -- Program Completed --")

if __name__ == "__main__":
    main()