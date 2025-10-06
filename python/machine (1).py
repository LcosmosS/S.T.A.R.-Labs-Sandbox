from sage.all import EllipticCurve, QQ, factor, prod, pi
import random
import pandas as pd
import numpy as np
from gplearn.genetic import SymbolicRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from cypari2 import Pari
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Increase PARI stack size to 3GB (balanced for MyBinder)
pari = Pari()
pari.allocatemem(3 * 1073741824)

# Fibonacci number generation
def generate_fibonacci(n):
    """Generate Fibonacci numbers up to index n."""
    fib = [0, 1]
    if n < 2:
        return fib[:n+1]
    for i in range(2, n+1):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def get_fibonacci_index(n, value):
    """Find the index of a Fibonacci number (or closest)."""
    fib_list = generate_fibonacci(n)
    return min(range(len(fib_list)), key=lambda i: abs(fib_list[i] - value))

def analyze_curve(a, b, max_bound=50):
    """Analyze elliptic curve and return features and 3-Selmer outcome."""
    features = {
        'a': a, 'b': b, 'a_index': get_fibonacci_index(50, a), 
        'b_index': get_fibonacci_index(50, b), 'discriminant': 0, 
        'conductor': 0, 'torsion_order': 1, '2_selmer_rank': 0, 
        'algebraic_rank': 0, 'a_over_b': a / b if b != 0 else 0
    }
    selmer_3_success = 0
    selmer_3_rank = None
    print(f"\nTesting curve: y² = x³ + {a}x + {b}")
    
    try:
        E = EllipticCurve(QQ, [0, 0, 0, a, b])
        features['discriminant'] = E.discriminant()
        features['conductor'] = E.conductor()
        features['torsion_order'] = E.torsion_subgroup().order()
        
        try:
            features['2_selmer_rank'] = E.selmer_rank()
            try:
                E.two_descent(second_limit=10, verbose=False)
                gens = E.gens()
                features['algebraic_rank'] = len(gens)
            except:
                points = E.points(bound=200)
                non_torsion = [p for p in points if p.order() == 0]
                features['algebraic_rank'] = max(1, len(non_torsion)) if non_torsion else 0
        except:
            features['algebraic_rank'] = 0
        
        try:
            S3 = E.selmer_group(3, [], proof=True, max_bound=max_bound)
            selmer_3_rank = len(S3) - 1
            selmer_3_success = 1
            print(f"3-Selmer rank: {selmer_3_rank} (3-sphere topological nodes)")
        except Exception as e:
            print(f"Failed to compute 3-Selmer rank: {e}")
            selmer_3_success = 0
    except Exception as e:
        print(f"Error creating/analyzing curve: {e}")
        return features, selmer_3_success, selmer_3_rank
    
    return features, selmer_3_success, selmer_3_rank

def collect_initial_data(n, num_pairs=20):
    """Collect initial data by testing random Fibonacci pairs."""
    fib_list = generate_fibonacci(n)
    data = []
    for _ in range(num_pairs):
        a, b = random.sample(fib_list, 2)
        features, selmer_3_success, selmer_3_rank = analyze_curve(a, b)
        features['selmer_3_success'] = selmer_3_success
        data.append(features)
    return pd.DataFrame(data)

def train_symbolic_regressor(data, n_iter_search=10):
    """Train SymbolicRegressor with hyperparameter tuning."""
    X = data[['a', 'b', 'a_index', 'b_index', 'discriminant', 'conductor', 
              'torsion_order', '2_selmer_rank', 'algebraic_rank', 'a_over_b']]
    y = data['selmer_3_success']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Define base model
    base_model = SymbolicRegressor(
        population_size=1000,
        generations=20,
        function_set=('add', 'sub', 'mul', 'div'),
        parsimony_coefficient=0.01,
        random_state=42
    )
    
    # Hyperparameter search space
    param_dist = {
        'population_size': [500, 1000, 2000],
        'generations': [10, 20, 30],
        'parsimony_coefficient': [0.001, 0.01, 0.1],
        'p_crossover': [0.7, 0.8, 0.9],
        'p_subtree_mutation': [0.1, 0.2],
        'p_hoist_mutation': [0.05, 0.1],
        'p_point_mutation': [0.1, 0.2]
    }
    
    # Perform randomized search
    search = RandomizedSearchCV(
        base_model,
        param_distributions=param_dist,
        n_iter=n_iter_search,
        cv=3,
        scoring='r2',
        random_state=42,
        n_jobs=1  # MyBinder has limited cores
    )
    search.fit(X_scaled, y)
    
    print(f"Best hyperparameters: {search.best_params_}")
    print(f"Best symbolic expression: {search.best_estimator_.program}")
    return search.best_estimator_, scaler

def predict_best_pairs(model, scaler, fib_list, num_candidates=5):
    """Predict and select top Fibonacci pairs for 3-Selmer success."""
    candidates = []
    for i in range(len(fib_list)):
        for j in range(i, len(fib_list)):
            a, b = fib_list[i], fib_list[j]
            features = {
                'a': a, 'b': b, 'a_index': i, 'b_index': j,
                'discriminant': 0, 'conductor': 0, 'torsion_order': 1,
                '2_selmer_rank': 0, 'algebraic_rank': 0,
                'a_over_b': a / b if b != 0 else 0
            }
            candidates.append(features)
    candidates_df = pd.DataFrame(candidates)
    X = candidates_df[['a', 'b', 'a_index', 'b_index', 'discriminant', 'conductor', 
                       'torsion_order', '2_selmer_rank', 'algebraic_rank', 'a_over_b']]
    X_scaled = scaler.transform(X)
    scores = model.predict(X_scaled)
    top_indices = np.argsort(scores)[-num_candidates:]
    return [(candidates_df.iloc[i]['a'], candidates_df.iloc[i]['b']) for i in top_indices]

# Main iterative search
n = 26
max_iterations = 50
initial_pairs = 20
fib_list = generate_fibonacci(n)
print(f"Fibonacci numbers up to index {n}: {fib_list}")

# Step 1: Collect initial data
print("\nCollecting initial data...")
data = collect_initial_data(n, initial_pairs)
print(f"Initial dataset size: {len(data)}")

# Step 2: Train symbolic regressor with hyperparameter tuning
print("\nTraining symbolic regressor with hyperparameter tuning...")
model, scaler = train_symbolic_regressor(data, n_iter_search=10)

# Step 3: Iterative search
iteration = 0
found_3_selmer = False
while iteration < max_iterations and not found_3_selmer:
    print(f"\nIteration {iteration + 1}/{max_iterations}")
    # Predict best pairs
    top_pairs = predict_best_pairs(model, scaler, fib_list, num_candidates=5)
    print(f"Testing top {len(top_pairs)} predicted pairs: {top_pairs}")
    
    # Test each pair
    for a, b in top_pairs:
        features, selmer_3_success, selmer_3_rank = analyze_curve(a, b)
        features['selmer_3_success'] = selmer_3_success
        data = pd.concat([data, pd.DataFrame([features])], ignore_index=True)
        if selmer_3_success:
            print(f"\nSuccess! Found 3-Selmer rank {selmer_3_rank} for curve y² = x³ + {a}x + {b}")
            found_3_selmer = True
            break
    
    # Retrain model with updated data
    if not found_3_selmer:
        print("\nRetraining symbolic regressor with updated data...")
        model, scaler = train_symbolic_regressor(data, n_iter_search=5)  # Fewer iterations for retraining
        iteration += 1

# Final result
if found_3_selmer:
    print(f"\nFound a curve with computable 3-Selmer rank after {iteration + 1} iterations.")
    print(f"Final symbolic expression: {model.program}")
else:
    print(f"\nFailed to find a curve with computable 3-Selmer rank after {max_iterations} iterations.")
print(f"Final dataset size: {len(data)}")
print(data.tail())