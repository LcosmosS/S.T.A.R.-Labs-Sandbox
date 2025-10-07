# # SageMath Pipeline Script for Deciphering Cosmological Generator Encoding (Version 7.3)
# 
# Stage 0: Setup and Configuration
# =================================

# --- CHANGE: REMOVED 'RuntimeError' FROM THE SAGE IMPORT, KEPT 'SignalError' ---
from sage.all import EllipticCurve, QQ, pari, Integer, SignalError
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import math

print("--- Pipeline Initialized ---")

VIRGO_CALIBRATED_KAPPA = 31.59259259259259

cluster_data = {
    'Coma': {'r': 321, 'rho': 9980},
    'Perseus': {'r': 236, 'rho': 11500}, 
    'Centaurus': {'r': 170, 'rho': 7500},
    'Virgo': {'r': 54, 'rho': 6320},
    'Hydra': {'r': 190, 'rho': 9000},
    'Leo': {'r': 330, 'rho': 8000},
    'Pavo-Indus': {'r': 230, 'rho': 10500},
    'Shapley': {'r': 650, 'rho': 18000},
    'Ursa Major': {'r': 60, 'rho': 2500},
    'Horologium': {'r': 700, 'rho': 12000},
    'Fornax': {'r': 62, 'rho': 3200},    
    'Hercules': {'r': 500, 'rho': 8500}
}

HOLDOUT_CLUSTER = 'Shapley'
print(f"Holdout cluster for final validation: {HOLDOUT_CLUSTER}")

# Stage 1: Foundational Dataset Generation
# =========================================
print("\n--- Stage 1: Generating Foundational Dataset ---")

def derive_and_analyze_cluster_curve(cluster_name, r, rho):
    print(f"\nProcessing cluster: {cluster_name}")
    try:
        a_predicted = -VIRGO_CALIBRATED_KAPPA * r
        b_predicted = rho
        if cluster_name == 'Virgo':
            a = -1706
        else:
            a = round(a_predicted)
        b = b_predicted
        print(f"  Derived curve: y^2 = x^3 + {a}x + {b}")
        
        E_sage = EllipticCurve(QQ, [a, b])
        
        try:
            rank = E_sage.rank(algorithm='pari')
        except RuntimeError as e:
            print(f"  SKIPPED: Rank computation failed with error: {e}")
            return None
            
        if rank == 1:
            generator = E_sage.gens()[0]
            print(f"  SUCCESS: Rank 1 curve found.")
            print(f"  Generator: {generator}")
            return {'cluster': cluster_name, 'r': r, 'rho': rho, 'a': a, 'b': b, 'rank': rank, 'generator': generator, 'curve_obj': E_sage}
        else:
            print(f"  SKIPPED: Predicted rank is {rank}, not 1.")
            return None
            
    except (SignalError, TypeError, ValueError) as e:
        print(f"  ERROR processing {cluster_name}: A low-level error occurred (likely a crash in the PARI library due to curve complexity). Skipping cluster. Error: {e}")
        return None

# (The rest of the script is unchanged)

analysis_results = []
for name, data in cluster_data.items():
    if name != HOLDOUT_CLUSTER:
        result = derive_and_analyze_cluster_curve(name, data['r'], data['rho'])
        if result:
            analysis_results.append(result)

holdout_result = derive_and_analyze_cluster_curve(HOLDOUT_CLUSTER, cluster_data[HOLDOUT_CLUSTER]['r'], cluster_data[HOLDOUT_CLUSTER]['rho'])
df = pd.DataFrame(analysis_results)

print("\n--- Stage 1 Complete: Foundational Dataset ---")
if not df.empty:
    df['x_coord'] = df['generator'].apply(lambda p: p[0])
    df['y_coord'] = df['generator'].apply(lambda p: p[1])
    df['x_num'] = df['x_coord'].apply(lambda x: x.numerator())
    df['x_den'] = df['x_coord'].apply(lambda x: x.denominator())
    df['y_num'] = df['y_coord'].apply(lambda y: y.numerator())
    df['y_den'] = df['y_coord'].apply(lambda y: y.denominator())
    print("Training Dataset:")
    print(df[['cluster', 'r', 'rho', 'generator']])
else:
    print("Training Dataset is empty.")

if holdout_result is None:
    print(f"\n\033[91mCRITICAL PIPELINE ERROR: Holdout cluster '{HOLDOUT_CLUSTER}' did not produce a Rank 1 curve.\033[0m")
    exit()

if df.empty or len(df) < 2:
    print(f"\n\033[91mCRITICAL PIPELINE ERROR: Training dataset has fewer than two points.\033[0m")
    exit()

# Stage 2: Adaptive Denominator Analysis
# =========================================
print("\n--- Stage 2: Adaptive Denominator Analysis ---")

def find_denominator_rule(denominators_df):
    non_one_denominators = (denominators_df != 1).sum().sum()
    total_denominators = denominators_df.size
    fractional_percentage = (non_one_denominators / total_denominators) * 100
    print(f"Analyzing training data denominators: {fractional_percentage:.2f}% are fractional.")
    if fractional_percentage > 50:
        print("Adopting 'Recursive' denominator rule based on Coma pattern.")
        return lambda n: 3**(2*n + 2)
    else:
        print("Adopting 'Simple' denominator rule based on integer pattern.")
        return lambda n: 1

denominator_func = find_denominator_rule(df[['x_den', 'y_den']])
print(f"Selected denominator function: f(1)={denominator_func(1)}, f(2)={denominator_func(2)}")
print("--- Stage 2 Complete ---")

# Stage 3: Modeling Numerators and Exchange Rate
# ===============================================================
print("\n--- Stage 3: Modeling Numerators and Exchange Rate ---")

df['exchange_rate'] = df['y_coord'] / df['r']
df['regulator'] = df['curve_obj'].apply(lambda E: E.regulator() if E.rank() > 0 else 1.0)
print("\nExchange Rate Analysis:")
print(df[['cluster', 'r', 'y_coord', 'exchange_rate', 'regulator']])

X_train = df[['r', 'rho']]
y_train_x_num = df['x_num']
y_train_y_num = df['y_num']
model_x_num = LinearRegression().fit(X_train, y_train_x_num)
model_y_num = LinearRegression().fit(X_train, y_train_y_num)

print("\nNumerator Model Coefficients (Linear):")
print(f"  x_num = {model_x_num.coef_[0]:.2f}*r + {model_x_num.coef_[1]:.2f}*rho + {model_x_num.intercept_:.2f}")
print(f"  y_num = {model_y_num.coef_[0]:.2f}*r + {model_y_num.coef_[1]:.2f}*rho + {model_y_num.intercept_:.2f}")
print("--- Stage 3 Complete ---")

# Stage 4: Synthesis and Predictive Validation
# ============================================
print("\n--- Stage 4: Synthesizing and Validating the Model ---")

def predict_generator(r, rho):
    predicted_x_num_numpy = model_x_num.predict(np.array([[r, rho]]))[0]
    predicted_y_num_numpy = model_y_num.predict(np.array([[r, rho]]))[0]
    py_float_x = predicted_x_num_numpy.item()
    py_float_y = predicted_y_num_numpy.item()
    predicted_x_den = denominator_func(1)
    predicted_y_den = denominator_func(2)
    sage_int_x = Integer(round(py_float_x))
    sage_int_y = Integer(round(py_float_y))
    predicted_x = QQ(sage_int_x, predicted_x_den)
    predicted_y = QQ(sage_int_y, predicted_y_den)
    return (predicted_x, predicted_y)

holdout_r = holdout_result['r']
holdout_rho = holdout_result['rho']
predicted_gen_coords = predict_generator(holdout_r, holdout_rho)

actual_gen = holdout_result['generator']
actual_gen_coords = (actual_gen[0], actual_gen[1])

print(f"\nValidation for Holdout Cluster: {HOLDOUT_CLUSTER}")
print(f"  Physical Inputs: r={holdout_r}, rho={holdout_rho}")
print(f"  Predicted Generator: {predicted_gen_coords}")
print(f"  Actual Generator:    {actual_gen_coords}")

x_match = (predicted_gen_coords[0] == actual_gen_coords[0])
y_match = (predicted_gen_coords[1] == actual_gen_coords[1])

if x_match and y_match:
    print("\nSUCCESS CRITERION MET: Predicted generator matches actual generator.")
else:
    print("\nSUCCESS CRITERION FAILED: Prediction does not match.")
    
print("\n--- Pipeline Finished ---")
