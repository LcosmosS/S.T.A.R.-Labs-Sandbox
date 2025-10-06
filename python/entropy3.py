# --- 1. Configuration --- 
INPUT_FILE = 'GalSpecExtra.csv' 
OUTPUT_PLOT_PREFIX = 'final_two_tier_synthesis_v47' 
CHUNKSIZE = 50000  # For ~18 chunks with 866,000 rows
ROW_LIMIT = 866000  # Matches dataset size
TARGET_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47] 
REQUIRED_COLUMNS = ['objid', 'ra', 'dec', 'z', 'logmass', 'petrorad_r', 'metallicity'] 
T_COSMO = 17.18 
REG_COSMO = 2.51 
KAPPA = 1.0 
SELMER_BOUND = 5 
MAX_CONDUCTOR = 10**8 
KB = 1.380649e-23  # Boltzmann constant (J/K) 
COHOMOLOGY_WEIGHT = 1e-3  # Scaling factor for Betti number 
ENTROPY_GRADIENT_WEIGHT = 1e-2  # Scaling factor for entropy gradient 
MAX_COHOM_POINTS = 500  # Subsample for memory in cdist

# --- 2. Imports --- 
import pandas as pd 
import numpy as np 
import warnings 
from astropy.cosmology import Planck18 as cosmo 
from astropy import units as u 
from sage.all import EllipticCurve, QQ, factor, parallel 
import matplotlib.pyplot as plt 
from matplotlib import animation
import seaborn as sns 
import altair as alt 
import plotly.express as px 
from sklearn.model_selection import cross_val_score 
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

warnings.filterwarnings('ignore') 
plt.style.use('seaborn-v0_8-whitegrid') 

print("          -- Initiating Program --")

# Logging to files
import logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG)
analysis_logger = logging.getLogger('analysis')
analysis_handler = logging.FileHandler('analysis.log')
analysis_logger.addHandler(analysis_handler)
analysis_logger.setLevel(logging.INFO)

# --- 3. Print Step Function ---
def print_step(step_num, step_name, summary=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[STEP {step_num}] {timestamp} - {step_name}")
    logging.info(f"Step {step_num}: {step_name}")
    if summary is not None:
        print(f"[SUMMARY {step_num}] {step_name} completed.")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        analysis_logger.info(f"Step {step_num} Summary: {summary}")

# --- 4. Pre-Calculation NaN Handling --- 
def impute_input_features(chunk, impute_cols=['ra', 'dec', 'z', 'metallicity'], target_cols=['logmass', 'petrorad_r']): 
    chunk = chunk.copy() 
    imputer = KNNImputer(n_neighbors=5, weights='distance') 
    X = chunk[impute_cols + target_cols] 
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=impute_cols + target_cols, index=chunk.index) 
    for target in target_cols: 
        nan_idx = chunk[target].isna() 
        if nan_idx.any(): 
            chunk.loc[nan_idx, target] = X_imputed.loc[nan_idx, target] 
            logging.debug(f"impute_input_features: Imputed {target} for {nan_idx.sum()} rows") 
    chunk['z'] = np.clip(chunk['z'], 1e-6, None)
    chunk['metallicity'] = np.clip(np.abs(chunk['metallicity']) + 1e-6, 1e-6, None)
    logging.debug(f"Clipped z_min={chunk['z'].min()}, met_min={chunk['metallicity'].min()}")
    return chunk 

# --- 5. Post-Calculation NaN Handling --- 
def impute_derived_features(df, feature_cols): 
    df = df.copy() 
    imputer = KNNImputer(n_neighbors=5, weights='distance') 
    X = df[feature_cols] 
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=feature_cols, index=df.index) 
    for col in feature_cols: 
        nan_idx = df[col].isna() 
        if nan_idx.any(): 
            df.loc[nan_idx, col] = X_imputed.loc[nan_idx, col] 
            logging.debug(f"impute_derived_features: Imputed {col} for {nan_idx.sum()} rows") 
    return df 

# --- 6. Thermodynamic Entropy Calculation --- 
def estimate_entropy(row, median_entropy=0): 
    from astropy.cosmology.units import redshift_temperature
    try:
        T_proxy = redshift_temperature(cosmo.Tcmb(0) * (1 + row['z'])).value 
        rho_proxy = max(1e-6, abs(row['metallicity']) * 1e-3)
        S = KB * np.log(T_proxy / (rho_proxy ** (2/3)))
        return S if np.isfinite(S) else median_entropy 
    except:
        return median_entropy 

# --- 7. Entropy Gradient Calculation --- 
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
    summary['Gradient Mean'] = np.mean(grad)
    analysis_logger.info("compute_entropy_gradient: Computed entropy gradient")
    return df, grad, summary

# --- 8. Cohomology Calculation --- 
def compute_cohomology(df, coords_cols=['ra', 'dec', 'z'], entropy_col='entropy', max_dimension=1): 
    if gudhi is None: 
        logging.warning("compute_cohomology: gudhi not installed. Returning NaN for betti_1") 
        summary = {'Status': 'gudhi not installed', 'Betti_1': 'NaN'}
        return df, np.full(len(df), np.nan), summary
    X_coords = df[coords_cols + [entropy_col]].dropna() 
    summary = {'Valid Rows': len(X_coords)}
    if X_coords.empty: 
        logging.warning("compute_cohomology: No valid coordinates for homology") 
        summary['Status': 'No valid coordinates'
        return df, np.full(len(df), np.nan), summary
    if len(X_coords) > MAX_COHOM_POINTS:
        X_coords = X_coords.sample(MAX_COHOM_POINTS, random_state=42)
        summary['Subsampled Rows'] = MAX_COHOM_POINTS
        logging.info(f"Subsampled to {MAX_COHOM_POINTS} points for cohomology")
    points = X_coords[coords_cols].values 
    weights = X_coords[entropy_col].values 
    dist = cdist(points, points) 
    w_rips = WeightedRipsComplex(distance_matrix=dist, weights=weights) 
    simplex_tree = w_rips.create_simplex_tree(max_dimension=max_dimension + 1) 
    persistence = simplex_tree.persistence() 
    betti_numbers = simplex_tree.betti_numbers() 
    betti_1 = betti_numbers[1] if len(betti_numbers) > 1 else 0 
    df['betti_1'] = np.nan 
    df.loc[X_coords.index, 'betti_1'] = betti_1 
    summary['Betti_1'] = betti_1
    analysis_logger.info(f"compute_cohomology: Betti_1 = {betti_1}")
    return df, betti_1, summary

# --- 9. KDE for Rank and L-Function --- 
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
    summary['KDE Density Mean'] = np.mean(log_dens)
    analysis_logger.info(f"compute_kde_features: Added KDE density for {rank_col} and {lfunc_col}")
    return df, log_dens, summary

# --- 10. Scientific Derivation Functions --- 
def calculate_distance_mpc(z): 
    if z is None or not np.isfinite(z) or z <= 0: 
        return np.nan 
    try: 
        return float(cosmo.comoving_distance(z).to(u.Mpc).value) 
    except: 
        return np.nan 

def convert_logmass_to_sm(logmass): 
    if not np.isfinite(logmass): 
        return np.nan 
    return 10**logmass 

def estimate_radius_ly(angular_size_arcsec, distance_mpc): 
    if not (np.isfinite(angular_size_arcsec) and np.isfinite(distance_mpc) and angular_size_arcsec > 0 and distance_mpc > 0): 
        return np.nan 
    angle_rad = (angular_size_arcsec * u.arcsec).to(u.rad).value 
    return angle_rad * distance_mpc * 3.262e6 

# --- 11. Elliptic Curve Calculations --- 
@parallel(ncpus=4)
def compute_3selmer_rank(delta, conductor, logmass, entropy, betti_1, entropy_gradient, pari): 
    entropy = 0 if np.isnan(entropy) else entropy
    betti_1 = 0 if np.isnan(betti_1) else betti_1
    entropy_gradient = 0 if np.isnan(entropy_gradient) else entropy_gradient
    if not all(np.isfinite(x) for x in [delta, conductor, logmass]): 
        logging.debug(f"compute_3selmer_rank: Skipped - Invalid delta={delta}, conductor={conductor}, logmass={logmass}") 
        return np.nan, 'invalid_input', np.nan, np.nan, np.nan 
    try: 
        scale_factor = max(1e3, np.log10(max(1, abs(delta)))) 
        delta_scaled = int(delta / scale_factor) 
        conductor_scaled = min(int(delta_scaled**2), MAX_CONDUCTOR) 
        if conductor_scaled > MAX_CONDUCTOR: 
            logging.debug(f"compute_3selmer_rank: Skipped - Scaled conductor={conductor_scaled} > MAX_CONDUCTOR") 
            return np.nan, 'large_conductor', np.nan, np.nan, np.nan 
        a = -delta_scaled 
        b = delta_scaled**2 + entropy * logmass + COHOMOLOGY_WEIGHT * betti_1 + ENTROPY_GRADIENT_WEIGHT * entropy_gradient 
        E = EllipticCurve(QQ, [0, 0, 0, a, b]).minimal_model() 
        rank = E.selmer_rank(3) 
        torsion = E.torsion_subgroup().order() 
        j_inv = E.j_invariant() 
        disc = E.discriminant() 
        analysis_logger.info(f"compute_3selmer_rank: logmass={logmass:.3f}, delta_scaled={delta_scaled}, conductor_scaled={conductor_scaled}, entropy={entropy:.3e}, betti_1={betti_1}, entropy_gradient={entropy_gradient:.3e}, rank={rank}")
        if rank > SELMER_BOUND: 
            logging.debug(f"compute_3selmer_rank: High rank={rank} > SELMER_BOUND={SELMER_BOUND}")
        return rank, 'success' if rank <= SELMER_BOUND else 'high_rank', torsion, j_inv, disc 
    except Exception as e: 
        logging.error(f"compute_3selmer_rank: Error - {str(e)}") 
        return np.nan, f'error_{str(e)}', np.nan, np.nan, np.nan 

# --- 12. Mapping Functions --- 
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
    entropy = estimate_entropy(row) 
    betti_1 = row.get('betti_1', np.nan) 
    entropy_gradient = row.get('entropy_gradient', np.nan) 
    selmer_rank, selmer_status, torsion, j_inv, disc = compute_3selmer_rank(delta, conductor, row['logmass'], entropy, betti_1, entropy_gradient, pari) 
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
    }) 

# --- 13. Generator Type Classification --- 
def classify_generator(row): 
    if pd.isna(row['log_delta']): 
        return 'unknown', False 
    is_simple = abs(row['log_delta'] - round(row['log_delta'])) < 0.1 
    return 'Simple' if is_simple else 'Recursive', is_simple 

# --- 14. Generator Structure Analysis --- 
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

# --- 15. Preprocess Clustering Features --- 
def preprocess_clustering_features(X_struct, feature_cols): 
    X_struct = X_struct.copy() 
    imputer = KNNImputer(n_neighbors=5, weights='distance') 
    X_struct[feature_cols] = imputer.fit_transform(X_struct[feature_cols]) 
    analysis_logger.info(f"preprocess_clustering_features: Imputed NaN in {feature_cols}")
    return X_struct 

# --- 16. Hyperparameter Optimization --- 
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

# --- 17. Symbolic Regression --- 
def run_symbolic_regression(X, y, feature_cols, method='pysr'): 
    if method == 'pysr' and PySRRegressor: 
        model = PySRRegressor( 
            niterations=40, 
            binary_operators=["+", "-", "*", "/"], 
            unary_operators=["log", "exp", "sqrt"], 
            maxsize=20, 
            model_selection="best" 
        ) 
        model.fit(X[feature_cols], y) 
        analysis_logger.info(f"PySR Equations:\n {model.equations_}")
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
        analysis_logger.info(f"GPlearn Equation:\n {model._program}")
        return model 
    else: 
        logging.warning(f"{method} not installed. Skipping symbolic regression.") 
        return None 

# --- 18. Interactive Visualization --- 
def interactive_visualization(df, feature_cols): 
    chart = alt.Chart(df).mark_circle().encode( 
        x=alt.X('selmer_rank:Q', title='3-Selmer Rank'), 
        y=alt.Y('betti_1:Q', title='Betti Number (H1)'), 
        color='generator_type:N', 
        size='entropy_gradient:Q', 
        tooltip=['objid', 'logmass', 'petrorad_r', 'selmer_rank', 'selmer_status', 'entropy', 'betti_1', 'entropy_gradient', 'kde_selmer_rank_var_ap'] 
    ).interactive().properties( 
        width=800, height=400, title='Rank vs. Cohomology (Betti_1) by Generator Type and Entropy Gradient' 
    ) 
    chart.save(f'{OUTPUT_PLOT_PREFIX}_interactive_scatter_cohomology.html') 
    fig = px.scatter_3d( 
        df, x='logmass', y='entropy', z='betti_1', 
        color='generator_type', size='entropy_gradient', 
        hover_data=['objid', 'selmer_rank', 'selmer_status', 'entropy', 'betti_1', 'entropy_gradient', 'kde_selmer_rank_var_ap'], 
        title='3D Galaxy Features with Cohomology and Entropy Gradient' 
    ) 
    fig.write_html(f'{OUTPUT_PLOT_PREFIX}_3d_scatter_cohomology.html') 
    if gudhi is not None: 
        X_coords = df[['ra', 'dec', 'z', 'entropy']].dropna() 
        if not X_coords.empty: 
            if len(X_coords) > MAX_COHOM_POINTS:
                X_coords = X_coords.sample(MAX_COHOM_POINTS, random_state=42)
            dist = cdist(X_coords[['ra', 'dec', 'z']], X_coords[['ra', 'dec', 'z']]) 
            w_rips = WeightedRipsComplex(distance_matrix=dist, weights=X_coords['entropy'].values) 
            simplex_tree = w_rips.create_simplex_tree(max_dimension=2) 
            persistence = simplex_tree.persistence() 
            plot_persistence_diagram(persistence) 
            plt.title('Persistence Diagram for Galaxy Coordinates (Entropy-Weighted)') 
            plt.savefig(f'{OUTPUT_PLOT_PREFIX}_persistence_diagram.png') 
            plt.close() 
    plt.figure(figsize=(10, 6)) 
    sns.scatterplot(data=df, x='entropy_gradient', y='betti_1', hue='generator_type', size='selmer_rank') 
    plt.title('Entropy Gradient vs. Betti_1 by Generator Type') 
    plt.savefig(f'{OUTPUT_PLOT_PREFIX}_entropy_gradient_betti1.png') 
    plt.close() 
    X_valid = df[feature_cols].dropna() 
    if not X_valid.empty: 
        tsne = TSNE(n_components=2, random_state=42, n_jobs=-1) 
        X_tsne = tsne.fit_transform(X_valid) 
        df_tsne = pd.DataFrame(X_tsne, columns=['TSNE1', 'TSNE2'], index=X_valid.index) 
        df_tsne['generator_type'] = df.loc[X_valid.index, 'generator_type'] 
        plt.figure(figsize=(10, 6)) 
        sns.scatterplot(data=df_tsne, x='TSNE1', y='TSNE2', hue='generator_type') 
        plt.title('t-SNE of Galaxy Features with Cohomology and Entropy Gradient') 
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_tsne_scatter_cohomology.png') 
        plt.close() 
    if not df.empty: 
        fig, ax = plt.subplots() 
        def animate(i): 
            ax.clear() 
            bin_df = df[(df['logmass'] > i) & (df['logmass'] <= i+1)] 
            sns.scatterplot(data=bin_df, x='entropy_gradient', y='betti_1', ax=ax) 
            ax.set_title(f'Entropy Gradient vs Betti_1 (logmass bin {i}-{i+1})') 
        anim = animation.FuncAnimation(fig, animate, frames=range(8,13), interval=500) 
        anim.save(f'{OUTPUT_PLOT_PREFIX}_entropy_gradient_video.mp4', writer='ffmpeg') 
        plt.close() 
    summary = {'Plots Generated': [
        'interactive_scatter_cohomology.html',
        '3d_scatter_cohomology.html',
        'entropy_gradient_betti1.png',
        'tsne_scatter_cohomology.png',
        'entropy_gradient_video.mp4'
    ]}
    if gudhi is not None:
        summary['Plots Generated'].append('persistence_diagram.png')
    return summary

# --- 19. Shape Analysis --- 
def analyze_noise_points(df, feature_cols): 
    recursive_df = df[df['generator_type'] == 'Recursive'] 
    noise_df = recursive_df[recursive_df['structure_cluster'] == -1] 
    clustered_df = recursive_df[recursive_df['structure_cluster'] != -1] 
    noise_stats = noise_df[feature_cols].describe() 
    clustered_stats = clustered_df[feature_cols].describe() 
    noise_nan_prop = noise_df[feature_cols].isna().mean() 
    clustered_nan_prop = clustered_df[feature_cols].isna().mean() 
    noise_structure_dist = noise_df['generator_structure'].apply(lambda x: x['structure'] if isinstance(x, dict) else 'unknown').value_counts() 
    clustered_structure_dist = clustered_df['generator_structure'].apply(lambda x: x['structure'] if isinstance(x, dict) else 'unknown').value_counts() 
    selmer_status_dist = df['selmer_status'].value_counts() 
    stats_df = pd.concat([noise_stats, clustered_stats], axis=1, keys=['Noise', 'Clustered']) 
    stats_df.to_csv(f'{OUTPUT_PLOT_PREFIX}_noise_vs_clustered_stats.csv') 
    noise_nan_prop.to_csv(f'{OUTPUT_PLOT_PREFIX}_noise_nan_proportion.csv') 
    clustered_nan_prop.to_csv(f'{OUTPUT_PLOT_PREFIX}_clustered_nan_proportion.csv') 
    noise_structure_dist.to_csv(f'{OUTPUT_PLOT_PREFIX}_noise_structure_distribution.csv') 
    clustered_structure_dist.to_csv(f'{OUTPUT_PLOT_PREFIX}_clustered_structure_distribution.csv') 
    selmer_status_dist.to_csv(f'{OUTPUT_PLOT_PREFIX}_selmer_status_distribution.csv') 
    summary = {
        'Noise Points': len(noise_df),
        'Clustered Points': len(clustered_df)
    }
    analysis_logger.info("Noise Points Statistics:\n" + str(noise_stats))
    analysis_logger.info("\nClustered Points Statistics:\n" + str(clustered_stats))
    analysis_logger.info("\nNoise Points NaN Proportion:\n" + str(noise_nan_prop))
    analysis_logger.info("\nClustered Points NaN Proportion:\n" + str(clustered_nan_prop))
    analysis_logger.info("\nNoise Points Structure Distribution:\n" + str(noise_structure_dist))
    analysis_logger.info("\nClustered Points Structure Distribution:\n" + str(clustered_structure_dist))
    analysis_logger.info("\nSelmer Status Distribution:\n" + str(selmer_status_dist))
    return summary

# --- 20. Chunk Processing Function --- 
def process_chunk(chunk, chunk_idx, total_chunks):
    print_step(20, f"process_chunk (Chunk {chunk_idx+1}/{total_chunks})")
    pari = cypari2.Pari()
    chunk = impute_input_features(chunk)
    chunk['ra'] = chunk['ra'].where(chunk['ra'].notna(), -1)
    chunk['dec'] = chunk['dec'].where(chunk['dec'].notna(), -1)
    chunk['distance_mpc'] = chunk['z'].apply(calculate_distance_mpc)
    chunk['stellar_mass'] = chunk['logmass'].apply(convert_logmass_to_sm)
    chunk['radius_ly'] = chunk.apply(lambda x: estimate_radius_ly(x['petrorad_r'], x['distance_mpc']), axis=1)
    chunk[['reg_cosmo', 't_cosmo', 'log_delta', 'log_omega', 'log_torsion',
           'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap',
           'sato_tate', 'isogeny_count', 'log_min_isogeny', 'log_torsion_type',
           'selmer_rank', 'selmer_status', 'torsion', 'j_invariant', 'discriminant', 'entropy', 'betti_1', 'entropy_gradient']] = chunk.apply(
               lambda x: compute_mappings(x, pari), axis=1)
    chunk[['generator_type', 'is_simple_generator']] = chunk.apply(classify_generator, axis=1, result_type='expand')
    chunk['generator_coords'] = chunk['log_delta'].apply(lambda x: (x, x*2) if not pd.isna(x) else np.nan)
    chunk['generator_structure'] = chunk['generator_coords'].apply(analyze_generator_structure)
    summary = {'Rows Processed': len(chunk)}
    print_step(20, f"process_chunk (Chunk {chunk_idx+1}/{total_chunks})", summary)
    return chunk

# --- 21. Cohomology Processing Function --- 
def process_cohomology(chunk, chunk_idx, total_chunks):
    print_step(21, f"process_cohomology (Chunk {chunk_idx+1}/{total_chunks})")
    chunk, betti_1, summary = compute_cohomology(chunk)
    print_step(21, f"process_cohomology (Chunk {chunk_idx+1}/{total_chunks})", summary)
    return chunk, betti_1

# --- 22. Main Processing --- 
def main(): 
    print_step(1, "Configuration")
    print_step(2, "Imports")
    print_step(22, "Main Processing")
    df = pd.read_csv(INPUT_FILE)
    df = df.iloc[:ROW_LIMIT]
    # Replace -9999 with NaN for logmass, sfr, metallicity
    for col in ['logmass', 'sfr', 'metallicity']:
        df[col] = df[col].replace(-9999, np.nan)
    summary = {'Initial Rows': len(df), 'NaN Counts': df[['logmass', 'sfr', 'metallicity']].isna().sum().to_dict()}
    print_step(22, "Data Loading", summary)

    # Drop NaN rows to test math (uncomment to enable)
    # df = df.dropna(subset=REQUIRED_COLUMNS[1:])
    # summary = {'Rows After Dropna': len(df)}
    # print_step(22, "Drop NaN", summary)

    print_step(20, "Chunk Processing")
    chunks = [df[i:i+CHUNKSIZE] for i in range(0, len(df), CHUNKSIZE)]
    total_chunks = len(chunks)
    with mp.Pool(processes=3) as pool:
        df_list = pool.starmap(process_chunk, [(chunk, idx, total_chunks) for idx, chunk in enumerate(chunks)])
    df = pd.concat(df_list, ignore_index=True)
    gc.collect()
    summary = {'Total Rows Processed': len(df), 'Chunks Processed': total_chunks}
    print_step(20, "Chunk Processing", summary)

    print_step(21, "Cohomology Processing")
    chunks = [df[i:i+CHUNKSIZE] for i in range(0, len(df), CHUNKSIZE)]
    with mp.Pool(processes=3) as pool:
        results = pool.starmap(process_cohomology, [(chunk, idx, total_chunks) for idx, chunk in enumerate(chunks)])
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
    analysis_logger.info("Generator Type Distribution:\n" + str(class_dist))
    summary = {'Generator Type Distribution': class_dist}
    print_step(22, "Check Class Distribution", summary)

    feature_cols = ['logmass', 'metallicity', 'petrorad_r', 'reg_cosmo', 't_cosmo', 'log_delta', 'log_omega',
                    'log_torsion', 'log_conductor', 'real_log_j', 'imag_log_j', 'tr_p1', 'var_ap', 'sato_tate',
                    'isogeny_count', 'log_min_isogeny', 'log_torsion_type', 'is_simple_generator', 'selmer_rank',
                    'torsion', 'j_invariant', 'discriminant', 'entropy', 'betti_1', 'entropy_gradient', 'kde_selmer_rank_var_ap']
    print_step(22, "Check NaN Counts")
    nan_counts = df[feature_cols].isna().sum().to_dict()
    analysis_logger.info("NaN Counts in Features:\n" + str(nan_counts))
    pd.Series(nan_counts).to_csv(f'{OUTPUT_PLOT_PREFIX}_nan_counts.csv')
    summary = {'NaN Counts': {k: v for k, v in nan_counts.items() if v > 0}}
    print_step(22, "Check NaN Counts", summary)

    print_step(5, "Impute Derived Features")
    df = impute_derived_features(df, feature_cols)
    summary = {'Rows Processed': len(df)}
    print_step(5, "Impute Derived Features", summary)

    X = df[feature_cols]
    y = df['generator_type']

    print_step(16, "Train Stacking Classifier")
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
    analysis_logger.info("Stacking Classifier Accuracy:" + str(gen_accuracy))
    analysis_logger.info("Classification Report:\n" + str(class_report))
    summary = {'Accuracy': gen_accuracy}
    print_step(16, "Train Stacking Classifier", summary)

    print_step(16, "Compute Generator Feature Importance")
    gen_perm_importance = permutation_importance(stacking_clf, X, y, n_repeats=10, random_state=42, n_jobs=-1)
    gen_feature_importance = pd.Series(gen_perm_importance.importances_mean, index=X.columns).sort_values(ascending=False)
    analysis_logger.info("\nGenerator Type Feature Importance:\n" + str(gen_feature_importance))
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
    X_struct = df[df['generator_type'] == 'Recursive'][['logmass', 'metallicity', 'petrorad_r', 'log_delta', 'log_omega', 'entropy', 'betti_1', 'entropy_gradient', 'kde_selmer_rank_var_ap']]
    summary = {'Recursive Rows': len(X_struct)}
    if not X_struct.empty:
        X_struct = preprocess_clustering_features(X_struct, ['logmass', 'metallicity', 'petrorad_r', 'log_delta', 'log_omega', 'entropy', 'betti_1', 'entropy_gradient', 'kde_selmer_rank_var_ap'])
        dbscan = DBSCAN(eps=0.5, min_samples=5, metric='nan_euclidean')
        cluster_labels = dbscan.fit_predict(X_struct)
        df.loc[df['generator_type'] == 'Recursive', 'structure_cluster'] = cluster_labels
        kmeans = KMeans(n_clusters=5, random_state=42, n_jobs=-1)
        kmeans_labels = kmeans.fit_predict(X_struct)
        df.loc[df['generator_type'] == 'Recursive', 'kmeans_cluster'] = kmeans_labels
        summary['DBSCAN Clusters'] = df[df['generator_type'] == 'Recursive']['structure_cluster'].value_counts().to_dict()
        summary['KMeans Clusters'] = df[df['generator_type'] == 'Recursive']['kmeans_cluster'].value_counts().to_dict()
        analysis_logger.info("Structure Clusters:" + str(summary['DBSCAN Clusters']))
        analysis_logger.info("KMeans Clusters:" + str(summary['KMeans Clusters']))
    print_step(15, "Perform Clustering", summary)

    print_step(19, "Analyze Noise Points")
    summary = analyze_noise_points(df, feature_cols)
    print_step(19, "Analyze Noise Points", summary)

    print_step(22, "Tully-Fisher Test")
    X_tf = df[feature_cols]
    y_tf = df['petrorad_r']
    valid_idx = y_tf.notna()
    X_tf = X_tf[valid_idx]
    y_tf = y_tf[valid_idx]
    analysis_logger.info(f"Tully-Fisher: Dropped {len(df) - len(X_tf)} rows due to NaN in petrorad_r")
    summary = {'Rows Dropped': len(df) - len(X_tf)}
    if not X_tf.empty:
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

        stacking_reg = StackingRegressor(estimators=regressors, final_estimator=HistGradientBoostingRegressor(random_state=42), n_jobs=-1)
        pipeline = Pipeline([
            ('scaler', StandardScaler(with_mean=False)),
            ('regressor', stacking_reg)
        ])
        pipeline.fit(X_tf, y_tf)
        tf_r2 = cross_val_score(pipeline, X_tf, y_tf, cv=5, scoring='r2', n_jobs=-1).mean()
        tf_perm_importance = permutation_importance(pipeline.named_steps['regressor'], X_tf, y_tf, n_repeats=10, random_state=42, n_jobs=-1)
        tf_feature_importance = pd.Series(tf_perm_importance.importances_mean, index=X_tf.columns).sort_values(ascending=False)
        analysis_logger.info("Tully-Fisher R²:" + str(tf_r2))
        analysis_logger.info("\nTully-Fisher Feature Importance:\n" + str(tf_feature_importance))
        tf_feature_importance.to_csv(f'{OUTPUT_PLOT_PREFIX}_tully_fisher_feature_importance.csv')
        summary['R²'] = tf_r2
        summary['Top Features'] = tf_feature_importance.head(5).to_dict()

        plt.figure(figsize=(10, 6))
        sns.barplot(x=tf_feature_importance.values, y=tf_feature_importance.index)
        plt.title('Tully-Fisher Feature Importance')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_tully_fisher_feature_importance.png')
        plt.close()

        for method in ['pysr', 'gplearn']:
            sym_reg_tf = run_symbolic_regression(X_tf, y_tf, feature_cols, method)
            if sym_reg_tf:
                getattr(sym_reg_tf, 'equations_', pd.DataFrame()).to_csv(f'{OUTPUT_PLOT_PREFIX}_symbolic_regression_tully_fisher_{method}.csv')
    print_step(22, "Tully-Fisher Test", summary)

    print_step(22, "Dimensionality Reduction")
    X_valid = df[feature_cols].dropna()
    summary = {'Valid Rows': len(X_valid)}
    if not X_valid.empty:
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_valid)
        df_pca = pd.DataFrame(X_pca, columns=['PC1', 'PC2'], index=X_valid.index)
        df_pca['generator_type'] = df.loc[X_valid.index, 'generator_type']
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df_pca, x='PC1', y='PC2', hue='generator_type')
        plt.title('PCA of Galaxy Features with Cohomology and Entropy Gradient')
        plt.savefig(f'{OUTPUT_PLOT_PREFIX}_pca_scatter_cohomology.png')
        plt.close()
        summary['PCA Variance Ratio'] = pca.explained_variance_ratio_.tolist()
    print_step(22, "Dimensionality Reduction", summary)

    print_step(18, "Interactive Visualization")
    summary = interactive_visualization(df, feature_cols)
    print_step(18, "Interactive Visualization", summary)

    print_step(22, "Save Results")
    df.to_csv(f'{OUTPUT_PLOT_PREFIX}_processed.csv', index=False)
    summary = {'Output File': f'{OUTPUT_PLOT_PREFIX}_processed.csv', 'Total Rows': len(df)}
    print_step(22, "Save Results", summary)
    gc.collect()

if __name__ == "__main__":
    main()