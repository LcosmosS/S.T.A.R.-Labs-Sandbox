# --- 1. Configuration ---
INPUT_FILE = 'merged_galspec_gz2.csv'
OUTPUT_PLOT_PREFIX = 'final_two_tier_synthesis_v28'
CHUNKSIZE = 100000
ROW_LIMIT = 300000  # Adjustable
TARGET_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
REQUIRED_COLUMNS = ['objid', 'ra', 'dec', 'z', 'logmass', 'petrorad_r', 'metallicity']
T_COSMO = 17.18
REG_COSMO = 2.51
KAPPA = 1.0  # Natural normalization

# --- 2. Imports ---
import pandas as pd
import numpy as np
import warnings
from astropy.cosmology import Planck18 as cosmo
from astropy import units as u
from sage.all import EllipticCurve, QQ, factor
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-whitegrid')

# --- 3. Scientific Derivation Functions ---
def calculate_distance_mpc(z):
    if z is None or not np.isfinite(z) or z <= 0:
        return np.nan
    try:
        return float(cosmo.comoving_distance(z).to(u.Mpc).value)
    except:
        return np.nan

def convert_logmass_to_sm(logmass):
    if logmass is None or not np.isfinite(logmass):
        return np.nan
    return 10**logmass

def estimate_radius_ly(angular_size_arcsec, distance_mpc):
    if not (np.isfinite(angular_size_arcsec) and np.isfinite(distance_mpc) and
            angular_size_arcsec > 0 and distance_mpc > 0):
        return np.nan
    angle_rad = (angular_size_arcsec * u.arcsec).to(u.rad).value
    return angle_rad * distance_mpc * 3.262e6

# --- 4. Mapping Functions ---
def compute_mappings(row):
    reg_cosmo = row['logmass'] * REG_COSMO * KAPPA if np.isfinite(row['logmass']) else np.nan
    t_cosmo = row['petrorad_r'] * T_COSMO * KAPPA if np.isfinite(row['petrorad_r']) else np.nan
    delta = row['logmass'] * 1e6 if np.isfinite(row['logmass']) else np.nan
    omega = row['petrorad_r'] * 1e3 if np.isfinite(row['petrorad_r']) else np.nan
    torsion_size = 1  # Placeholder (Mazur’s classification)
    conductor = delta**2 if np.isfinite(delta) else np.nan
    j_invariant = row['metallicity'] * 1e4 if np.isfinite(row['metallicity']) else np.nan
    tr_p1 = float(factor(int(delta))[0][0]) if np.isfinite(delta) and delta != 0 else np.nan
    tr_p2 = float(factor(int(delta * 2))[0][0]) if np.isfinite(delta) and delta != 0 else np.nan
    tr_p3 = float(factor(int(delta * 3))[0][0]) if np.isfinite(delta) and delta != 0 else np.nan
    var_ap = np.var([tr_p1, tr_p2, tr_p3]) if all(np.isfinite([tr_p1, tr_p2, tr_p3])) else np.nan
    sato_tate = float(TARGET_PRIMES[0] * np.arccos(tr_p1 / (2 * np.sqrt(TARGET_PRIMES[0])))) if np.isfinite(tr_p1) and tr_p1 != 0 else np.nan
    isogeny_count = 1  # Placeholder
    min_isogeny_deg = 1
    torsion_type = torsion_size
    return pd.Series({
        'reg_cosmo': reg_cosmo,
        't_cosmo': t_cosmo,
        'log_delta': np.log(abs(delta)) if np.isfinite(delta) and delta != 0 else np.nan,
        'log_omega': np.log(abs(omega)) if np.isfinite(omega) and omega != 0 else np.nan,
        'log_torsion': np.log(1 + torsion_size),
        'log_conductor': np.log(abs(conductor)) if np.isfinite(conductor) and conductor != 0 else np.nan,
        'real_log_j': np.log(abs(j_invariant)) if np.isfinite(j_invariant) and j_invariant != 0 else np.nan,
        'imag_log_j': 0.0,  # Mock, assuming real j-invariant
        'tr_p1': tr_p1,
        'var_ap': var_ap,
        'sato_tate': sato_tate,
        'isogeny_count': isogeny_count,
        'log_min_isogeny': np.log(min_isogeny_deg) if min_isogeny_deg != 0 else np.nan,
        'log_torsion_type': np.log(1 + torsion_type)
    })

# --- 5. Generator Type Classification and Boolean Metric ---
def classify_generator(row):
    if pd.isna(row['log_delta']):
        return 'unknown', False
    is_simple = abs(row['log_delta'] - round(row['log_delta'])) < 0.1
    return 'Simple' if is_simple else 'Recursive', is_simple

# --- 6. Generator Structure Analysis ---
def analyze_generator_structure(coords):
    if pd.isna(coords):
        return {'type': 'unknown', 'structure': 'unknown'}
    x, y = coords if isinstance(coords, tuple) else (np.nan, np.nan)
    if pd.isna(x) or pd.isna(y):
        return {'type': 'unknown', 'structure': 'unknown'}
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and float(x).is_integer() and float(y).is_integer():
        return {'type': 'Simple', 'structure': 'integer'}
    denom_x = x.denominator() if hasattr(x, 'denominator') else 1
    denom_y = y.denominator() if hasattr(y, 'denominator') else 1
    factors_x = factor(denom_x) if denom_x != 1 else []
    if len(factors_x) == 1 and len(factors_x[0][0].prime_factors()) == 1:
        return {'type': 'Recursive', 'structure': 'power_of_prime'}
    return {'type': 'Recursive', 'structure': 'other_sequence'}

# --- 7. Infer Missing Values Using Deciphered Metrics ---
def infer_missing_values(df, cluster_labels, feature_cols, is_simple_col):
    df = df.copy()
    # Handle Recursive generators
    recursive_idx = df[df['generator_type'] == 'Recursive'].index
    if cluster_labels is not None and len(np.unique(cluster_labels)) > 1:
        X_recursive = df.loc[recursive_idx, feature_cols].values
        mask = np.isnan(X_recursive)
        if mask.any():
            nbrs = NearestNeighbors(n_neighbors=5, metric='nan_euclidean').fit(X_recursive)
            for row_idx in range(X_recursive.shape[0]):
                if mask[row_idx].any():
                    distances, indices = nbrs.kneighbors([X_recursive[row_idx]], return_distance=True)
                    valid_indices = indices[0][cluster_labels[indices[0]] == cluster_labels[row_idx]]
                    if len(valid_indices) > 0:
                        neighbor_values = X_recursive[valid_indices]
                        X_recursive[row_idx, mask[row_idx]] = np.nanmean(neighbor_values[:, mask[row_idx]], axis=0)
            df.loc[recursive_idx, feature_cols] = X_recursive
    # Handle Simple generators
    simple_idx = df[df[is_simple_col] == True].index
    if not simple_idx.empty:
        X_simple = df.loc[simple_idx, feature_cols].values
        mask = np.isnan(X_simple)
        if mask.any():
            nbrs = NearestNeighbors(n_neighbors=5, metric='nan_euclidean').fit(X_simple)
            for row_idx in range(X_simple.shape[0]):
                if mask[row_idx].any():
                    distances, indices = nbrs.kneighbors([X_simple[row_idx]], return_distance=True)
                    valid_indices = indices[0]
                    if len(valid_indices) > 0:
                        neighbor_values = X_simple[valid_indices]
                        X_simple[row_idx, mask[row_idx]] = np.nanmean(neighbor_values[:, mask[row_idx]], axis=0)
            df.loc[simple_idx, feature_cols] = X_simple
    return df

# --- 8. Main Processing ---
chunks = pd.read_csv(INPUT_FILE, usecols=REQUIRED_COLUMNS, chunksize=CHUNKSIZE)
df_list = []
for i, chunk in enumerate(chunks):
    if ROW_LIMIT and i * CHUNKSIZE >= ROW_LIMIT:
        break
    chunk['ra'] = chunk['ra'].where(chunk['ra'].notna(), -1)
    chunk['dec'] = chunk['dec'].where(chunk['dec'].notna(), -1)
    
    chunk['distance_mpc'] = chunk['z'].apply(calculate_distance_mpc)
    chunk['stellar_mass'] = chunk['logmass'].apply(convert_logmass_to_sm)
    chunk['radius_ly'] = chunk.apply(lambda x: estimate_radius_ly(x['petrorad_r'], x['distance_mpc']), axis=1)
    chunk[['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion',
           'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap',
           'sato_tate', 'isogeny_count', 'log_min_isogeny', 'log_torsion_type']] = chunk.apply(compute_mappings, axis=1)
    
    chunk[['generator_type', 'is_simple_generator']] = chunk.apply(classify_generator, axis=1, result_type='expand')
    chunk['generator_coords'] = chunk['log_delta'].apply(lambda x: (x, x*2) if not pd.isna(x) else np.nan)
    chunk['generator_structure'] = chunk['generator_coords'].apply(analyze_generator_structure)
    
    df_list.append(chunk)

df = pd.concat(df_list, ignore_index=True)

# Bin by generator type
X = df[['logmass', 'metallicity', 'petrorad_r', 'reg_cosmo', 't_cosmo', 'log_delta', 'log_omega',
        'log_torsion', 'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap', 'sato_tate',
        'isogeny_count', 'log_min_isogeny', 'log_torsion_type', 'is_simple_generator']]
y = df['generator_type']

clf_gen = HistGradientBoostingClassifier(random_state=42)
clf_gen.fit(X, y)
print("Generator Type Accuracy:", cross_val_score(clf_gen, X, y, cv=5).mean())

# Unsupervised clustering for generator structure
X_struct = df[df['generator_type'] == 'Recursive'][['logmass', 'metallicity', 'petrorad_r', 'log_delta', 'log_omega']]
cluster_labels = None
if not X_struct.empty:
    dbscan = DBSCAN(eps=0.5, min_samples=5, metric='nan_euclidean')
    cluster_labels = dbscan.fit_predict(X_struct)
    df.loc[df['generator_type'] == 'Recursive', 'structure_cluster'] = cluster_labels
    print("Structure Clusters:", df[df['generator_type'] == 'Recursive']['structure_cluster'].value_counts())
else:
    print("No Recursive generators found for clustering.")

# Infer missing values using deciphered metrics
feature_cols = ['logmass', 'metallicity', 'petrorad_r', 'reg_cosmo', 't_cosmo', 'log_delta', 'log_omega',
                'log_torsion', 'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap', 'sato_tate',
                'isogeny_count', 'log_min_isogeny', 'log_torsion_type']
df = infer_missing_values(df, cluster_labels, feature_cols, 'is_simple_generator')

# Tully-Fisher test
X_tf = df[['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion', 'log_conductor',
           'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap', 'sato_tate', 'isogeny_count', 'log_min_isogeny', 'is_simple_generator']]
y_tf = df['petrorad_r']
pipeline = Pipeline([
    ('scaler', StandardScaler(with_mean=False)),  # with_mean=False to handle NaN
    ('regressor', HistGradientBoostingRegressor(random_state=42))
])
pipeline.fit(X_tf, y_tf)
print("Tully-Fisher R²:", cross_val_score(pipeline, X_tf, y_tf, cv=5, scoring='r2').mean())

# Save results
df.to_csv(f'{OUTPUT_PLOT_PREFIX}_processed.csv', index=False)

