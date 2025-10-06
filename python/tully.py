# --- 1. Configuration ---
INPUT_FILE = 'merged_galspec_gz2.csv'
OUTPUT_PLOT_PREFIX = 'final_two_tier_synthesis_v22'
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
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import DBSCAN
import lightgbm as lgb
from imblearn.over_sampling import SMOTE

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-whitegrid')

# --- 3. Scientific Derivation Functions ---
def calculate_distance_mpc(z):
    if z is None or not np.isfinite(z) or z <= 0:
        return np.nan
    try:
        return cosmo.comoving_distance(z).to(u.Mpc).value
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
    # BSD analogue
    reg_cosmo = row['logmass'] * REG_COSMO * KAPPA
    t_cosmo = row['petrorad_r'] * T_COSMO * KAPPA
    # PTD Mapping
    delta = row['logmass'] * 1e6  # Mock
    omega = row['petrorad_r'] * 1e3
    torsion_size = 1  # Placeholder
    # MCJ Mapping
    conductor = delta**2
    j_invariant = row['metallicity'] * 1e4
    # FT Mapping
    tr_p1 = factor(int(delta))[0][0] if delta != 0 else 0
    tr_p2 = factor(int(delta * 2))[0][0] if delta != 0 else 0
    tr_p3 = factor(int(delta * 3))[0][0] if delta != 0 else 0
    var_ap = np.var([tr_p1, tr_p2, tr_p3])
    sato_tate = TARGET_PRIMES[0] * np.arccos(tr_p1 / (2 * np.sqrt(TARGET_PRIMES[0]))) if tr_p1 != 0 else 0
    # IWT Mapping
    isogeny_count = 1  # Placeholder
    min_isogeny_deg = 1
    torsion_type = torsion_size
    return pd.Series({
        'reg_cosmo': reg_cosmo,
        't_cosmo': t_cosmo,
        'log_delta': np.log(abs(delta)) if delta != 0 else np.nan,
        'log_omega': np.log(abs(omega)) if omega != 0 else np.nan,
        'log_torsion': np.log(1 + torsion_size),
        'log_conductor': np.log(abs(conductor)) if conductor != 0 else np.nan,
        'real_log_j': np.log(abs(j_invariant)) if j_invariant != 0 else np.nan,
        'imag_log_j': 0,  # Mock, assuming real j-invariant
        'tr_p1': tr_p1,
        'var_ap': var_ap,
        'sato_tate': sato_tate,
        'isogeny_count': isogeny_count,
        'log_min_isogeny': np.log(min_isogeny_deg) if min_isogeny_deg != 0 else np.nan,
        'log_torsion_type': np.log(1 + torsion_type)
    })

# --- 5. Generator Type Classification ---
def classify_generator(row):
    if pd.isna(row['log_delta']):
        return 'unknown'
    return 'Simple' if abs(row['log_delta'] - round(row['log_delta'])) < 0.1 else 'Recursive'

# --- 6. Generator Structure Analysis ---
def analyze_generator_structure(coords):
    if pd.isna(coords):
        return {'type': 'unknown', 'structure': 'unknown'}
    x, y = coords if isinstance(coords, tuple) else (np.nan, np.nan)
    if pd.isna(x) or pd.isna(y):
        return {'type': 'unknown', 'structure': 'unknown'}
    if x.is_integer() and y.is_integer():
        return {'type': 'Simple', 'structure': 'integer'}
    denom_x = x.denominator() if hasattr(x, 'denominator') else 1
    denom_y = y.denominator() if hasattr(y, 'denominator') else 1
    factors_x = factor(denom_x) if denom_x != 1 else []
    if len(factors_x) == 1 and len(factors_x[0][0].prime_factors()) == 1:
        return {'type': 'Recursive', 'structure': 'power_of_prime'}
    return {'type': 'Recursive', 'structure': 'other_sequence'}

# --- 7. Main Processing ---
chunks = pd.read_csv(INPUT_FILE, usecols=REQUIRED_COLUMNS, chunksize=CHUNKSIZE)
df_list = []
for i, chunk in enumerate(chunks):
    if ROW_LIMIT and i * CHUNKSIZE >= ROW_LIMIT:
        break
    # Impute NaN values
    chunk['logmass'].fillna(chunk['logmass'].median(), inplace=True)
    chunk['metallicity'].fillna(chunk['metallicity'].median(), inplace=True)
    chunk['petrorad_r'].fillna(chunk['petrorad_r'].median(), inplace=True)
    chunk['ra'].fillna(-1, inplace=True)
    chunk['dec'].fillna(-1, inplace=True)
    chunk['z'].fillna(chunk['z'].median(), inplace=True)
    
    # Compute distances and mappings
    chunk['distance_mpc'] = chunk['z'].apply(calculate_distance_mpc)
    chunk['stellar_mass'] = chunk['logmass'].apply(convert_logmass_to_sm)
    chunk['radius_ly'] = chunk.apply(lambda x: estimate_radius_ly(x['petrorad_r'], x['distance_mpc']), axis=1)
    chunk[['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion',
           'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap',
           'sato_tate', 'isogeny_count', 'log_min_isogeny', 'log_torsion_type']] = chunk.apply(compute_mappings, axis=1)
    
    # Classify generator types
    chunk['generator_type'] = chunk.apply(classify_generator, axis=1)
    chunk['generator_coords'] = chunk['log_delta'].apply(lambda x: (x, x*2) if not pd.isna(x) else np.nan)
    chunk['generator_structure'] = chunk['generator_coords'].apply(analyze_generator_structure)
    
    df_list.append(chunk)

df = pd.concat(df_list, ignore_index=True)

# Bin by generator type
X = df[['logmass', 'metallicity', 'petrorad_r', 'reg_cosmo', 't_cosmo', 'log_delta', 'log_omega',
        'log_torsion', 'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap', 'sato_tate',
        'isogeny_count', 'log_min_isogeny', 'log_torsion_type']]
y = df['generator_type']
smote = SMOTE(random_state=42)
X_balanced, y_balanced = smote.fit_resample(X, y)

# Train classifier for generator type
clf_gen = RandomForestClassifier(random_state=42)
clf_gen.fit(X_balanced, y_balanced)
print("Generator Type Accuracy:", cross_val_score(clf_gen, X, y, cv=5).mean())

# Unsupervised clustering for generator structure
X_struct = df[df['generator_type'] == 'Recursive'][['logmass', 'metallicity', 'petrorad_r', 'log_delta', 'log_omega']]
dbscan = DBSCAN(eps=0.5, min_samples=5)
df.loc[df['generator_type'] == 'Recursive', 'structure_cluster'] = dbscan.fit_predict(X_struct)
print("Structure Clusters:", df[df['generator_type'] == 'Recursive']['structure_cluster'].value_counts())

# Tully-Fisher test
X_tf = df[['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion', 'log_conductor',
           'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap', 'sato_tate', 'isogeny_count', 'log_min_isogeny']]
y_tf = df['petrorad_r']
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', lgb.LGBMRegressor(random_state=42))
])
pipeline.fit(X_tf, y_tf)
print("Tully-Fisher R²:", cross_val_score(pipeline, X_tf, y_tf, cv=5, scoring='r2').mean())

# Save results
df.to_csv(f'{OUTPUT_PLOT_PREFIX}_processed.csv', index=False)
