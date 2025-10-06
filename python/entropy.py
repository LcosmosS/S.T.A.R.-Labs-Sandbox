# --- 1. Configuration ---
INPUT_FILE = 'merged_galspec_gz2.csv'
OUTPUT_PLOT_PREFIX = 'final_two_tier_synthesis_v40'
CHUNKSIZE = 100000
ROW_LIMIT = 300000
TARGET_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
REQUIRED_COLUMNS = ['objid', 'ra', 'dec', 'z', 'logmass', 'petrorad_r', 'metallicity']
T_COSMO = 17.18
REG_COSMO = 2.51
KAPPA = 1.0
SELMER_BOUND = 5
MAX_CONDUCTOR = 10**8
KB = 1.380649e-23  # Boltzmann constant (J/K)

# --- 2. Imports ---
import pandas as pd
import numpy as np
import warnings
from astropy.cosmology import Planck18 as cosmo
from astropy import units as u
from sage.all import EllipticCurve, QQ, factor, parallel
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import plotly.express as px
import ipywidgets as widgets
from IPython.display import display
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, classification_report
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor, StackingClassifier, StackingRegressor
from sklearn.cluster import DBSCAN, KMeans
from sklearn.impute import KNNImputer
from sklearn.inspection import permutation_importance
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
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
    from cypari2 import Pari
except ImportError:
    print("cypari2 not installed. Run: mamba install cypari2 -c conda-forge")
    exit(1)

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-whitegrid')

# --- 3. Function Tracking ---
def log_function(func_name):
    print(f"Running {func_name}...")

# --- 4. Pre-Calculation NaN Handling ---
def impute_input_features(chunk, impute_cols=['ra', 'dec', 'z', 'metallicity'], target_cols=['logmass', 'petrorad_r']):
    log_function("impute_input_features")
    chunk = chunk.copy()
    imputer = KNNImputer(n_neighbors=5, weights='distance')
    X = chunk[impute_cols + target_cols]
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=impute_cols + target_cols, index=chunk.index)
    for target in target_cols:
        nan_idx = chunk[target].isna()
        if nan_idx.any():
            chunk.loc[nan_idx, target] = X_imputed.loc[nan_idx, target]
            print(f"impute_input_features: Imputed {target} for {nan_idx.sum()} rows")
    return chunk

# --- 5. Thermodynamic Entropy Calculation ---
def estimate_entropy(row):
    log_function("estimate_entropy")
    # Proxy entropy: S = k * ln(T / ρ^(2/3)), where T ∝ z, ρ ∝ metallicity
    if not (np.isfinite(row['z']) and np.isfinite(row['metallicity']) and row['metallicity'] > 0):
        return np.nan
    T_proxy = row['z'] * 1e7  # Approximate temperature (K) from redshift
    rho_proxy = row['metallicity'] * 1e-3  # Approximate density (kg/m^3)
    try:
        S = KB * np.log(T_proxy / (rho_proxy ** (2/3)))
        return S
    except:
        return np.nan

# --- 6. Scientific Derivation Functions ---
def calculate_distance_mpc(z):
    log_function("calculate_distance_mpc")
    if z is None or not np.isfinite(z) or z <= 0:
        return np.nan
    try:
        return float(cosmo.comoving_distance(z).to(u.Mpc).value)
    except:
        return np.nan

def convert_logmass_to_sm(logmass):
    log_function("convert_logmass_to_sm")
    if not np.isfinite(logmass):
        return np.nan
    return 10**logmass

def estimate_radius_ly(angular_size_arcsec, distance_mpc):
    log_function("estimate_radius_ly")
    if not (np.isfinite(angular_size_arcsec) and np.isfinite(distance_mpc) and
            angular_size_arcsec > 0 and distance_mpc > 0):
        return np.nan
    angle_rad = (angular_size_arcsec * u.arcsec).to(u.rad).value
    return angle_rad * distance_mpc * 3.262e6

# --- 7. Elliptic Curve Calculations ---
@parallel
def compute_3selmer_rank(delta, conductor, logmass, entropy, pari):
    log_function("compute_3selmer_rank")
    if not np.isfinite(delta) or not np.isfinite(conductor) or not np.isfinite(logmass) or not np.isfinite(entropy):
        print(f"compute_3selmer_rank: Skipped - Invalid delta={delta}, conductor={conductor}, logmass={logmass}, entropy={entropy}")
        return np.nan, 'invalid_input', np.nan, np.nan, np.nan
    try:
        scale_factor = max(1e3, delta / np.sqrt(MAX_CONDUCTOR))
        delta_scaled = int(delta / scale_factor)
        conductor_scaled = delta_scaled**2
        if conductor_scaled > MAX_CONDUCTOR:
            print(f"compute_3selmer_rank: Skipped - Scaled conductor={conductor_scaled} > MAX_CONDUCTOR")
            return np.nan, 'large_conductor', np.nan, np.nan, np.nan
        # Modulate b with entropy
        a = -delta_scaled
        b = delta_scaled**2 + entropy * logmass  # Entropy term
        E = EllipticCurve(QQ, [0, 0, 0, a, b])
        rank = E.selmer_rank(3)
        torsion = E.torsion_subgroup().order()
        j_inv = E.j_invariant()
        disc = E.discriminant()
        print(f"compute_3selmer_rank: logmass={logmass:.3f}, delta_scaled={delta_scaled}, conductor_scaled={conductor_scaled}, entropy={entropy:.3e}, rank={rank}")
        if rank > SELMER_BOUND:
            print(f"compute_3selmer_rank: High rank={rank} > SELMER_BOUND={SELMER_BOUND}")
            return rank, 'high_rank', torsion, j_inv, disc
        return rank, 'success', torsion, j_inv, disc
    except Exception as e:
        print(f"compute_3selmer_rank: Error - {str(e)}")
        return np.nan, f'error_{str(e)}', np.nan, np.nan, np.nan

# --- 8. Mapping Functions ---
def compute_mappings(row, pari):
    log_function("compute_mappings")
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
    entropy = estimate_entropy(row)
    selmer_rank, selmer_status, torsion, j_inv, disc = compute_3selmer_rank(delta, conductor, row['logmass'], entropy, pari)
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
        'entropy': entropy
    })

# --- 9. Generator Type Classification ---
def classify_generator(row):
    log_function("classify_generator")
    if pd.isna(row['log_delta']):
        return 'unknown', False
    is_simple = abs(row['log_delta'] - round(row['log_delta'])) < 0.1
    return 'Simple' if is_simple else 'Recursive', is_simple

# --- 10. Generator Structure Analysis ---
def analyze_generator_structure(coords):
    log_function("analyze_generator_structure")
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

# --- 11. Preprocess Clustering Features ---
def preprocess_clustering_features(X_struct, feature_cols):
    log_function("preprocess_clustering_features")
    X_struct = X_struct.copy()
    imputer = KNNImputer(n_neighbors=5, weights='distance')
    X_struct[feature_cols] = imputer.fit_transform(X_struct[feature_cols])
    print(f"preprocess_clustering_features: Imputed NaN in {feature_cols}")
    return X_struct

# --- 12. Hyperparameter Optimization ---
def optimize_catboost_classifier(X, y, n_trials=50):
    log_function("optimize_catboost_classifier")
    if CatBoostClassifier is None or create_study is None:
        print("CatBoost or Optuna not installed. Skipping optimization.")
        return None
    def objective(trial):
        params = {
            'iterations': trial.suggest_int('iterations', 100, 1000),
            'depth': trial.suggest_int('depth', 4, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 10)
        }
        model = CatBoostClassifier(**params, verbose=0)
        return cross_val_score(model, X, y, cv=5).mean()
    study = create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials)
    return study.best_params

def optimize_catboost_regressor(X, y, n_trials=50):
    log_function("optimize_catboost_regressor")
    if CatBoostRegressor is None or create_study is None:
        print("CatBoost or Optuna not installed. Skipping optimization.")
        return None
    def objective(trial):
        params = {
            'iterations': trial.suggest_int('iterations', 100, 1000),
            'depth': trial.suggest_int('depth', 4, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 10)
        }
        model = CatBoostRegressor(**params, verbose=0)
        return cross_val_score(model, X, y, cv=5, scoring='r2').mean()
    study = create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials)
    return study.best_params

# --- 13. Symbolic Regression ---
def run_symbolic_regression(X, y, feature_cols, method='pysr'):
    log_function(f"run_symbolic_regression_{method}")
    if method == 'pysr' and PySRRegressor:
        model = PySRRegressor(
            niterations=40,
            binary_operators=["+", "-", "*", "/"],
            unary_operators=["log", "exp", "sqrt"],
            maxsize=20,
            model_selection="best"
        )
        model.fit(X[feature_cols], y)
        print(f"PySR Equations:\n", model.equations_)
        return model
    elif method == 'gplearn' and SymbolicRegressor:
        model = SymbolicRegressor(
            population_size=1000,
            generations=20,
            function_set=('add', 'sub', 'mul', 'div', 'log', 'sqrt'),
            metric='mse',
            random_state=42
        )
        model.fit(X[feature_cols], y)
        print(f"GPlearn Equation:\n", model._program)
        return model
    else:
        print(f"{method} not installed. Skipping symbolic regression.")
        return None

# --- 14. Interactive Visualization ---
def interactive_visualization(df, feature_cols):
    log_function("interactive_visualization")
    # Altair scatter plot
    chart = alt.Chart(df).mark_circle().encode(
        x=alt.X('logmass:Q', title='Log Stellar Mass'),
        y=alt.Y('entropy:Q', title='Entropy (J/K)'),
        color='generator_type:N',
        tooltip=['objid', 'logmass', 'petrorad_r', 'selmer_rank', 'selmer_status', 'entropy']
    ).interactive().properties(
        width=800, height=400, title='Galaxy Features with Entropy by Generator Type'
    )
    chart.save(f'{OUTPUT_PLOT_PREFIX}_interactive_scatter_entropy.html')

    # Plotly 3D scatter plot
    fig = px.scatter_3d(
        df, x='logmass', y='petrorad_r', z='entropy',
        color='generator_type', size='selmer_rank',
        hover_data=['objid', 'selmer_rank', 'selmer_status', 'entropy'],
        title='3D Galaxy Features with Entropy'
    )
    fig.write_html(f'{OUTPUT_PLOT_PREFIX}_3d_scatter_entropy.html')

    # t-SNE visualization
    X_valid = df[feature_cols].dropna()
    if not X_valid.empty:
        tsne = TSNE(n_components=2, random_state=42)
        X_tsne = tsne.fit_transform(X_valid)
        df_tsne = pd.DataFrame(X_tsne, columns=['TSNE1', 'TSNE2'], index=X_valid.index)
        df_tsne['generator_type'] = df.loc[X_valid.index, 'generator_type']
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df_tsne, x='TSNE1', y='TSNE2', hue='generator_type')
        plt.title('t-SNE of Galaxy Features with Entropy')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_tsne_scatter_entropy.png')
        plt.close()

    # Interactive widget
    @widgets.interact(feature=feature_cols)
    def plot_histogram(feature):
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x=feature, hue='generator_type', bins=50)
        plt.title(f'Distribution of {feature} by Generator Type')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_histogram_{feature}.png')
        plt.show()

# --- 15. Shape Analysis ---
def analyze_noise_points(df, feature_cols):
    log_function("analyze_noise_points")
    recursive_df = df[df['generator_type'] == 'Recursive']
    noise_df = recursive_df[recursive_df['structure_cluster'] == -1]
    clustered_df = recursive_df[recursive_df['structure_cluster'] != -1]
    
    noise_stats = noise_df[feature_cols].describe()
    clustered_stats = clustered_df[feature_cols].describe()
    noise_nan_prop = noise_df[feature_cols].isna().mean()
    clustered_nan_prop = clustered_df[feature_cols].isna().mean()
    noise_structure_dist = noise_df['generator_structure'].apply(lambda x: x['structure'] if isinstance(x, dict) else 'unknown').value_counts()
    clustered_structure_dist = clustered_df['generator_structure'].apply(lambda x: x['structure'] if isinstance(x, dict) else 'unknown').value_counts()
    selmer_status_dist = df[df['generator_type'] == 'Recursive']['selmer_status'].value_counts()
    
    stats_df = pd.concat([noise_stats, clustered_stats], axis=1, keys=['Noise', 'Clustered'])
    stats_df.to_csv(f'{OUTPUT_PLOT_PREFIX}_noise_vs_clustered_stats.csv')
    noise_nan_prop.to_csv(f'{OUTPUT_PLOT_PREFIX}_noise_nan_proportion.csv')
    clustered_nan_prop.to_csv(f'{OUTPUT_PLOT_PREFIX}_clustered_nan_proportion.csv')
    noise_structure_dist.to_csv(f'{OUTPUT_PLOT_PREFIX}_noise_structure_distribution.csv')
    clustered_structure_dist.to_csv(f'{OUTPUT_PLOT_PREFIX}_clustered_structure_distribution.csv')
    selmer_status_dist.to_csv(f'{OUTPUT_PLOT_PREFIX}_selmer_status_distribution.csv')
    
    print("Noise Points Statistics:\n", noise_stats)
    print("\nClustered Points Statistics:\n", clustered_stats)
    print("\nNoise Points NaN Proportion:\n", noise_nan_prop)
    print("\nClustered Points NaN Proportion:\n", clustered_nan_prop)
    print("\nNoise Points Structure Distribution:\n", noise_structure_dist)
    print("\nClustered Points Structure Distribution:\n", clustered_structure_dist)
    print("\nSelmer Status Distribution:\n", selmer_status_dist)

# --- 16. Main Processing ---
def main():
    log_function("main")
    pari = Pari()
    chunks = pd.read_csv(INPUT_FILE, usecols=REQUIRED_COLUMNS, chunksize=CHUNKSIZE)
    df_list = []
    for i, chunk in enumerate(chunks):
        if ROW_LIMIT and i * CHUNKSIZE >= ROW_LIMIT:
            break
        log_function("process_chunk")
        chunk = impute_input_features(chunk)
        
        chunk['ra'] = chunk['ra'].where(chunk['ra'].notna(), -1)
        chunk['dec'] = chunk['dec'].where(chunk['dec'].notna(), -1)
        
        chunk['distance_mpc'] = chunk['z'].apply(calculate_distance_mpc)
        chunk['stellar_mass'] = chunk['logmass'].apply(convert_logmass_to_sm)
        chunk['radius_ly'] = chunk.apply(lambda x: estimate_radius_ly(x['petrorad_r'], x['distance_mpc']), axis=1)
        chunk[['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion',
               'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap',
               'sato_tate', 'isogeny_count', 'log_min_isogeny', 'log_torsion_type',
               'selmer_rank', 'selmer_status', 'torsion', 'j_invariant', 'discriminant', 'entropy']] = chunk.apply(
                   lambda x: compute_mappings(x, pari), axis=1)
        
        chunk[['generator_type', 'is_simple_generator']] = chunk.apply(classify_generator, axis=1, result_type='expand')
        chunk['generator_coords'] = chunk['log_delta'].apply(lambda x: (x, x*2) if not pd.isna(x) else np.nan)
        chunk['generator_structure'] = chunk['generator_coords'].apply(analyze_generator_structure)
        
        df_list.append(chunk)

    df = pd.concat(df_list, ignore_index=True)

    # Check class distribution
    log_function("check_class_distribution")
    print("Generator Type Distribution:\n", df['generator_type'].value_counts())

    # Machine learning models for generator type
    feature_cols = ['logmass', 'metallicity', 'petrorad_r', 'reg_cosmo', 't_cosmo', 'log_delta', 'log_omega',
                    'log_torsion', 'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap', 'sato_tate',
                    'isogeny_count', 'log_min_isogeny', 'log_torsion_type', 'is_simple_generator', 'selmer_rank',
                    'torsion', 'j_invariant', 'discriminant', 'entropy']
    X = df[feature_cols]
    y = df['generator_type']

    # Optimize CatBoost
    catboost_params_clf = optimize_catboost_classifier(X, y) if CatBoostClassifier and create_study else None
    classifiers = [
        ('RandomForest', RandomForestClassifier(random_state=42)),
        ('GradientBoosting', GradientBoostingClassifier(random_state=42))
    ]
    if XGBClassifier:
        classifiers.append(('XGBoost', XGBClassifier(random_state=42)))
    if LGBMClassifier:
        classifiers.append(('LightGBM', LGBMClassifier(random_state=42)))
    if CatBoostClassifier and catboost_params_clf:
        classifiers.append(('CatBoost', CatBoostClassifier(**catboost_params_clf, verbose=0)))

    stacking_clf = StackingClassifier(estimators=classifiers, final_estimator=GradientBoostingClassifier(random_state=42))
    stacking_clf.fit(X, y)
    gen_accuracy = cross_val_score(stacking_clf, X, y, cv=5).mean()
    print("Stacking Classifier Accuracy:", gen_accuracy)
    print("Classification Report:\n", classification_report(y, stacking_clf.predict(X)))

    # Feature importance
    log_function("compute_generator_feature_importance")
    gen_perm_importance = permutation_importance(stacking_clf, X, y, n_repeats=10, random_state=42)
    gen_feature_importance = pd.Series(gen_perm_importance.importances_mean, index=X.columns).sort_values(ascending=False)
    print("\nGenerator Type Feature Importance:\n", gen_feature_importance)
    gen_feature_importance.to_csv(f'{OUTPUT_PLOT_PREFIX}_generator_feature_importance.csv')

    plt.figure(figsize=(10, 6))
    sns.barplot(x=gen_feature_importance.values, y=gen_feature_importance.index)
    plt.title('Generator Type Feature Importance')
    plt.savefig(f'{OUTPUT_PLOT_PREFIX}_generator_feature_importance.png')
    plt.close()

    # Symbolic regression for generator type
    log_function("symbolic_regression_generator")
    for method in ['pysr', 'gplearn']:
        sym_reg_gen = run_symbolic_regression(X, y.map({'Simple': 0, 'Recursive': 1, 'unknown': 2}), feature_cols, method)
        if sym_reg_gen:
            getattr(sym_reg_gen, 'equations_', pd.DataFrame()).to_csv(f'{OUTPUT_PLOT_PREFIX}_symbolic_regression_generator_{method}.csv')

    # Clustering
    log_function("perform_clustering")
    X_struct = df[df['generator_type'] == 'Recursive'][['logmass', 'metallicity', 'petrorad_r', 'log_delta', 'log_omega', 'entropy']]
    cluster_labels = None
    if not X_struct.empty:
        X_struct = preprocess_clustering_features(X_struct, ['logmass', 'metallicity', 'petrorad_r', 'log_delta', 'log_omega', 'entropy'])
        dbscan = DBSCAN(eps=0.5, min_samples=5, metric='nan_euclidean')
        cluster_labels = dbscan.fit_predict(X_struct)
        df.loc[df['generator_type'] == 'Recursive', 'structure_cluster'] = cluster_labels
        print("Structure Clusters:", df[df['generator_type'] == 'Recursive']['structure_cluster'].value_counts())

        kmeans = KMeans(n_clusters=5, random_state=42)
        kmeans_labels = kmeans.fit_predict(X_struct)
        df.loc[df['generator_type'] == 'Recursive', 'kmeans_cluster'] = kmeans_labels
        print("KMeans Clusters:", df[df['generator_type'] == 'Recursive']['kmeans_cluster'].value_counts())

    # Shape analysis
    analyze_noise_points(df, feature_cols)

    # Tully-Fisher test
    log_function("tully_fisher_test")
    X_tf = df[feature_cols]
    y_tf = df['petrorad_r']
    valid_idx = y_tf.notna()
    X_tf = X_tf[valid_idx]
    y_tf = y_tf[valid_idx]
    print(f"Tully-Fisher: Dropped {len(df) - len(X_tf)} rows due to NaN in petrorad_r")
    if not X_tf.empty:
        catboost_params_reg = optimize_catboost_regressor(X_tf, y_tf) if CatBoostRegressor and create_study else None
        regressors = [
            ('RandomForest', RandomForestRegressor(random_state=42)),
            ('GradientBoosting', GradientBoostingRegressor(random_state=42))
        ]
        if XGBRegressor:
            regressors.append(('XGBoost', XGBRegressor(random_state=42)))
        if LGBMRegressor:
            regressors.append(('LightGBM', LGBMRegressor(random_state=42)))
        if CatBoostRegressor and catboost_params_reg:
            regressors.append(('CatBoost', CatBoostRegressor(**catboost_params_reg, verbose=0)))

        stacking_reg = StackingRegressor(estimators=regressors, final_estimator=GradientBoostingRegressor(random_state=42))
        pipeline = Pipeline([
            ('scaler', StandardScaler(with_mean=False)),
            ('regressor', stacking_reg)
        ])
        pipeline.fit(X_tf, y_tf)
        tf_r2 = cross_val_score(pipeline, X_tf, y_tf, cv=5, scoring='r2').mean()
        print("Tully-Fisher R²:", tf_r2)

        tf_perm_importance = permutation_importance(pipeline.named_steps['regressor'], X_tf, y_tf, n_repeats=10, random_state=42)
        tf_feature_importance = pd.Series(tf_perm_importance.importances_mean, index=X_tf.columns).sort_values(ascending=False)
        print("\nTully-Fisher Feature Importance:\n", tf_feature_importance)
        tf_feature_importance.to_csv(f'{OUTPUT_PLOT_PREFIX}_tully_fisher_feature_importance.csv')

        plt.figure(figsize=(10, 6))
        sns.barplot(x=tf_feature_importance.values, y=tf_feature_importance.index)
        plt.title('Tully-Fisher Feature Importance')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_tully_fisher_feature_importance.png')
        plt.close()

        for method in ['pysr', 'gplearn']:
            sym_reg_tf = run_symbolic_regression(X_tf, y_tf, feature_cols, method)
            if sym_reg_tf:
                getattr(sym_reg_tf, 'equations_', pd.DataFrame()).to_csv(f'{OUTPUT_PLOT_PREFIX}_symbolic_regression_tully_fisher_{method}.csv')

    # PCA and t-SNE
    log_function("dimensionality_reduction")
    X_valid = df[feature_cols].dropna()
    if not X_valid.empty:
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_valid)
        df_pca = pd.DataFrame(X_pca, columns=['PC1', 'PC2'], index=X_valid.index)
        df_pca['generator_type'] = df.loc[X_valid.index, 'generator_type']
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df_pca, x='PC1', y='PC2', hue='generator_type')
        plt.title('PCA of Galaxy Features with Entropy')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_pca_scatter_entropy.png')
        plt.close()

    # Interactive visualization
    interactive_visualization(df, feature_cols)

    # Save results
    log_function("save_results")
    df.to_csv(f'{OUTPUT_PLOT_PREFIX}_processed.csv', index=False)

if __name__ == "__main__":
    main()
