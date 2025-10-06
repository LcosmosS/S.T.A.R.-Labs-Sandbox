import numpy as np
import pandas as pd
from sage.all import EllipticCurve, QQ
from lightgbm import LGBMRegressor, LGBMClassifier
from gplearn.genetic import SymbolicRegressor
import optuna
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import warnings
warnings.filterwarnings("ignore")

# Sample dataset from prior SageMath runs
data = {
    'a': [610, 1597, 4181, 6765, -1706],
    'b': [987, 2584, 6765, 10946, 6320],
    'rank': [2, 2, 0, 0, 1],
    '2_selmer': [2, 2, 0, 0, 1],
    '3_selmer_success': [0, 0, 0, 0, 0],
    'conductor': [14947625008, 263556691264, 4697342528624, 1277409456, 150258963712],
    'L1': [41.909771622141768890247990872, 109.33501270486232639659441304, 11.623958153320433114775999495, 3.2924373801657142866068441027, 5.7161472701821916623395660050],
    'scaled_density': [1324.34878325968, 3454.98640147365, 367.317077644926, 104.116011748013, 180.630253737757]
}
df = pd.DataFrame(data)
df['discriminant'] = -16 * (4 * df['a']**3 + 27 * df['b']**2)
df['a_b_ratio'] = df['a'] / df['b']
df['log_a'] = np.log1p(df['a'].abs())
df['log_b'] = np.log1p(df['b'].abs())

# SageMath function to compute curve invariants
def compute_invariants(a, b):
    try:
        E = EllipticCurve(QQ, [0, 0, 0, a, b])
        rank = E.rank() if E.rank() is not None else -1
        selmer_2 = E.selmer_rank()
        selmer_3_success = 1
        try:
            E.selmer_group(3, [])
        except:
            selmer_3_success = 0
        conductor = E.conductor()
        L = E.lseries()
        L1 = L.dokchitser(prec=50)(1) if abs(L.dokchitser(prec=50)(1)) > 1e-10 else L.dokchitser(prec=50).derivative(1, 1)
        scaled_density = L1 * (1000 ** 0.5)
        return {'rank': rank, '2_selmer': selmer_2, '3_selmer_success': selmer_3_success,
                'conductor': conductor, 'L1': L1, 'scaled_density': scaled_density}
    except:
        return None

# ML pipeline
def train_predictor(X, y, task='regression'):
    model = LGBMRegressor() if task == 'regression' else LGBMClassifier()
    model.fit(X, y)
    return model

# Objective function for Optuna
def objective(trial, X, y, target_name):
    params = {
        'num_leaves': trial.suggest_int('num_leaves', 10, 100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'n_estimators': trial.suggest_int('n_estimators', 50, 500)
    }
    model = LGBMRegressor(**params) if target_name in ['L1', 'scaled_density', 'conductor'] else LGBMClassifier(**params)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_val)
    score = mean_squared_error(y_val, y_pred) if target_name in ['L1', 'scaled_density', 'conductor'] else model.score(X_val, y_val)
    return score

# Symbolic regression
def symbolic_regressor(X, y):
    est = SymbolicRegressor(population_size=500, generations=20, function_set=('add', 'sub', 'mul', 'div', 'sqrt', 'log'))
    est.fit(X, y)
    return est

# Main pipeline
X = df[['a', 'b', 'discriminant', 'a_b_ratio', 'log_a', 'log_b']]
targets = ['rank', '2_selmer', '3_selmer_success', 'conductor', 'L1', 'scaled_density']

# Train predictors
models = {}
for target in targets:
    task = 'regression' if target in ['conductor', 'L1', 'scaled_density'] else 'classification'
    models[target] = train_predictor(X, df[target], task)

# Optimize with Optuna
studies = {}
for target in targets:
    study = optuna.create_study(direction='minimize' if target in ['conductor', 'L1', 'scaled_density'] else 'maximize')
    study.optimize(lambda trial: objective(trial, X, df[target], target), n_trials=50)
    studies[target] = study

# Symbolic regression for rank and L1
sym_rank = symbolic_regressor(X, df['rank'])
sym_L1 = symbolic_regressor(X, df['L1'])
print(f"Symbolic rank model: {sym_rank._program}")
print(f"Symbolic L1 model: {sym_L1._program}")

# Continuous testing
fibonacci = generate_fibonacci(26)
for i in range(15, 25):
    a, b = fibonacci[i], fibonacci[i+1]
    X_new = pd.DataFrame({
        'a': [a], 'b': [b], 'discriminant': [-16 * (4 * a**3 + 27 * b**2)],
        'a_b_ratio': [a/b], 'log_a': [np.log1p(abs(a))], 'log_b': [np.log1p(abs(b))]
    })
    predicted = {t: models[t].predict(X_new)[0] for t in targets}
    if predicted['3_selmer_success'] < 0.5 or predicted['rank'] < 2:
        # Adjust coefficients
        a_new = a * (1 + np.random.uniform(-0.1, 0.1))
        b_new = b * (1 + np.random.uniform(-0.1, 0.1))
        X_new['a'], X_new['b'] = a_new, b_new
        X_new['discriminant'] = -16 * (4 * a_new**3 + 27 * b_new**2)
        X_new['a_b_ratio'] = a_new / b_new
        X_new['log_a'], X_new['log_b'] = np.log1p(abs(a_new)), np.log1p(abs(b_new))
        predicted = {t: models[t].predict(X_new)[0] for t in targets}
    # Validate with SageMath
    invariants = compute_invariants(a_new, b_new)
    if invariants and invariants['3_selmer_success'] == 1 and invariants['scaled_density'] > 5000:
        print(f"Success: a={a_new}, b={b_new}, invariants={invariants}")
        break