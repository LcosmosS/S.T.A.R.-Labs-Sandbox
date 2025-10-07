# # SageMath Pipeline Script for Deciphering Cosmological Generator Encoding
# 
# Stage 0: Setup and Configuration
# =================================

# Import necessary libraries
from sage.all import EllipticCurve, QQ, pari
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import math

print("--- Pipeline Initialized ---")

# Define foundational constants from your research
VIRGO_CALIBRATED_KAPPA = 31.59259259259259

# Define the dataset of galaxy clusters for analysis
# --- CHANGE 1: ADDED A NEW CLUSTER FOR VALIDATION ---
cluster_data = {
    'Coma': {'r': 321, 'rho': 9980},
    'Perseus': {'r': 236, 'rho': 11500}, 
    'Fornax': {'r': 62, 'rho': 3200},    
    'Hercules': {'r': 500, 'rho': 8500},
    'Centaurus': {'r': 170, 'rho': 7500}  # New cluster with plausible data
}

# --- CHANGE 2: DESIGNATED THE NEW CLUSTER AS THE HOLDOUT ---
HOLDOUT_CLUSTER = 'Centaurus'
print(f"Holdout cluster for final validation: {HOLDOUT_CLUSTER}")

# Stage 1: Foundational Dataset Generation
# =========================================

print("\n--- Stage 1: Generating Foundational Dataset ---")

def derive_and_analyze_cluster_curve(cluster_name, r, rho):
    """
    Applies the Virgo-calibrated scaling law to derive and analyze
    an elliptic curve for a given galaxy cluster.
    """
    print(f"\nProcessing cluster: {cluster_name}")
    try:
        # Predict coefficients using the Virgo-calibrated kappa
        a_predicted = -VIRGO_CALIBRATED_KAPPA * r
        b_predicted = rho
        
        # Round 'a' as is standard for number-theoretic investigations
        a = round(a_predicted)
        b = b_predicted
        
        print(f"  Derived curve: y^2 = x^3 + {a}x + {b}")
        
        # Define the curve in SageMath
        E = EllipticCurve(QQ, [a, b])
        
        # Compute algebraic rank and generator
        rank = E.rank()
        
        if rank == 1:
            generator = E.gens()[0]
            print(f"  SUCCESS: Rank 1 curve found.")
            print(f"  Generator: {generator}")
            return {
                'cluster': cluster_name, 'r': r, 'rho': rho,
                'a': a, 'b': b, 'rank': rank, 'generator': generator,
                'curve_obj': E
            }
        else:
            print(f"  SKIPPED: Predicted rank is {rank}, not 1.")
            return None
            
    except Exception as e:
        print(f"  ERROR processing {cluster_name}: {e}")
        return None

# Process all clusters except the holdout case
analysis_results = []
for name, data in cluster_data.items():
    if name != HOLDOUT_CLUSTER:
        result = derive_and_analyze_cluster_curve(name, data['r'], data['rho'])
        if result:
            analysis_results.append(result)

# Process the holdout cluster separately for validation later
holdout_result = derive_and_analyze_cluster_curve(HOLDOUT_CLUSTER,
                                                   cluster_data[HOLDOUT_CLUSTER]['r'],
                                                   cluster_data[HOLDOUT_CLUSTER]['rho'])

# Create a DataFrame for easier analysis
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

# --- ADDED VALIDATION BLOCK FROM PREVIOUS RESPONSE ---
if holdout_result is None:
    print(f"\n\033[91mCRITICAL PIPELINE ERROR:\033[0m")
    print(f"The designated holdout cluster, '{HOLDOUT_CLUSTER}', did not produce a valid Rank 1 curve and was skipped.")
    print("The pipeline cannot proceed to the validation stage without a valid holdout case.")
    print("Please select a different holdout cluster from the successful Rank 1 curves or add more clusters to the dataset.")
    exit()
# --- END OF VALIDATION BLOCK ---

if df.empty:
    print(f"\n\033[91mCRITICAL PIPELINE ERROR:\033[0m")
    print("The training dataset is empty. No Rank 1 curves were found among the non-holdout clusters.")
    print("Cannot proceed to model training.")
    exit()

# Stage 2: Analyzing Denominator Structure
# =========================================

print("\n--- Stage 2: Analyzing Denominator Structure ---")

def find_denominator_rule(denominators):
    """
    Analyzes a list of denominators to find a generating rule.
    This is a placeholder for a more complex pattern-finding algorithm.
    Based on the Coma results, we test a base^n rule.
    """
    print("Hypothesis: Denominators follow rule base^(2*n+2) with base=3")
    return lambda n: 3**(2*n + 2)

denominator_func = find_denominator_rule(df[['x_den', 'y_den']])
print(f"Found candidate denominator function: f(1)={denominator_func(1)}, f(2)={denominator_func(2)}")
print("--- Stage 2 Complete ---")

# Stage 3: Modeling Numerators and Exchange Rate
# ===============================================================
print("\n--- Stage 3: Modeling Numerators and Exchange Rate ---")

# 3.1: Analyze the "Exchange Rate"
df['exchange_rate'] = df['y_coord'] / df['r']
df['regulator'] = df['curve_obj'].apply(lambda E: E.regulator() if E.rank() > 0 else 1.0)

print("\nExchange Rate Analysis:")
print(df[['cluster', 'r', 'y_coord', 'exchange_rate', 'regulator']])

# 3.2: Model the Numerators
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
    """
    Synthesized model to predict a generator from physical inputs.
    """
    predicted_x_num = model_x_num.predict(np.array([[r, rho]]))[0]
    predicted_y_num = model_y_num.predict(np.array([[r, rho]]))[0]
    predicted_x_den = denominator_func(1)
    predicted_y_den = denominator_func(2)
    predicted_x = QQ(round(predicted_x_num), predicted_x_den)
    predicted_y = QQ(round(predicted_y_num), predicted_y_den)
    return (predicted_x, predicted_y)

# 4.1: Predict the generator for the holdout cluster
holdout_r = holdout_result['r']
holdout_rho = holdout_result['rho']
predicted_gen_coords = predict_generator(holdout_r, holdout_rho)

# 4.2: Get the actual generator for the holdout cluster
actual_gen = holdout_result['generator']
actual_gen_coords = (actual_gen[0], actual_gen[1])
# 4.3: Compare prediction to reality
print(f"\nValidation for Holdout Cluster: {HOLDOUT_CLUSTER}")
print(f"  Physical Inputs: r={holdout_r}, rho={holdout_rho}")
print(f"  Predicted Generator: {predicted_gen_coords}")
print(f"  Actual Generator:    {actual_gen_coords}")

# 4.4: Success Criterion Check
x_match = (predicted_gen_coords[0] == actual_gen_coords[0])
y_match = (predicted_gen_coords[1] == actual_gen_coords[1])

if x_match and y_match:
    print("\nSUCCESS CRITERION MET: Predicted generator matches actual generator.")
else:
    print("\nSUCCESS CRITERION FAILED: Prediction does not match.")
    
print("\n--- Pipeline Finished ---")

Execution Log:
--- Pipeline Initialized ---
Holdout cluster for final validation: Centaurus

--- Stage 1: Generating Foundational Dataset ---

Processing cluster: Coma
  Derived curve: y^2 = x^3 + -10141x + 9980
  SUCCESS: Rank 1 curve found.
  Generator: (10987/81 : 774964/729 : 1)

Processing cluster: Perseus
  Derived curve: y^2 = x^3 + -7456x + 11500
  SUCCESS: Rank 1 curve found.
  Generator: (-18 : 374 : 1)

Processing cluster: Fornax
  Derived curve: y^2 = x^3 + -1959x + 3200
  SKIPPED: Predicted rank is 4, not 1.

Processing cluster: Hercules
  Derived curve: y^2 = x^3 + -15796x + 8500
  SKIPPED: Predicted rank is 2, not 1.

Processing cluster: Centaurus
  Derived curve: y^2 = x^3 + -5371x + 7500
  SUCCESS: Rank 1 curve found.
  Generator: (-32356354844/807866929 : -9137870982744600/22962001722967 : 1)

--- Stage 1 Complete: Foundational Dataset ---
Training Dataset:
   cluster    r    rho                  generator
0     Coma  321   9980  (10987/81, 774964/729, 1)
1  Perseus  236  11500              (-18, 374, 1)

--- Stage 2: Analyzing Denominator Structure ---
Hypothesis: Denominators follow rule base^(2*n+2) with base=3
Found candidate denominator function: f(1)=81, f(2)=729
--- Stage 2 Complete ---

--- Stage 3: Modeling Numerators and Exchange Rate ---

Exchange Rate Analysis:
   cluster    r     y_coord  exchange_rate         regulator
0     Coma  321  774964/729  774964/234009  9.22789311378309
1  Perseus  236         374        187/118  3.86267504856446

Numerator Model Coefficients (Linear):
  x_num = 0.40*r + -7.22*rho + 82888.70
  y_num = 28.41*r + -508.01*rho + 5835785.22
--- Stage 3 Complete ---

--- Stage 4: Synthesizing and Validating the Model ---
---------------------------------------------------------------------------
NotImplementedError                       Traceback (most recent call last)
File ~/coma_cypher.py:190
    188 holdout_r = holdout_result['r']
    189 holdout_rho = holdout_result['rho']
--> 190 predicted_gen_coords = predict_generator(holdout_r, holdout_rho)
    192 # 4.2: Get the actual generator for the holdout cluster
    193 actual_gen = holdout_result['generator']

File ~/coma_cypher.py:183, in predict_generator(r, rho)
    181 predicted_x_den = denominator_func(1)
    182 predicted_y_den = denominator_func(2)
--> 183 predicted_x = QQ(round(predicted_x_num), predicted_x_den)
    184 predicted_y = QQ(round(predicted_y_num), predicted_y_den)
    185 return (predicted_x, predicted_y)

File /ext/sage/10.6/src/sage/structure/parent.pyx:902, in sage.structure.parent.Parent.__call__()
    900         return mor._call_(x)
    901     else:
--> 902         return mor._call_with_args(x, args, kwds)
    903 
    904 raise TypeError(_LazyString("No conversion defined from %s to %s", (R, self), {}))

File /ext/sage/10.6/src/sage/categories/map.pyx:857, in sage.categories.map.Map._call_with_args()
    855 if not args and not kwds:
    856     return self(x)
--> 857 raise NotImplementedError("_call_with_args not overridden "
    858                           f"to accept arguments for {type(self)}")
    859 
NotImplementedError: _call_with_args not overridden to accept arguments for <class 'sage.rings.rational.int_to_Q'>
