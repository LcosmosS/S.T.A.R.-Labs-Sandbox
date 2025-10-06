import numpy as np
import pandas as pd
from sage.all import EllipticCurve, QQ
from lightgbm import LGBMRegressor, LGBMClassifier
from gplearn.genetic import SymbolicRegressor
import optuna
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error
from cypari2 import Pari
import warnings
warnings.filterwarnings("ignore")

# Increase PARI stack size
pari = Pari()
pari.allocatemem(2 * 1073741824)

# Fibonacci generator
def generate_fibonacci(n):
    """Generate Fibonacci numbers up to index n."""
    fib = [0, 1]
    if n < 2:
        return fib[:n+1]
    for i in range(2, n+1):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# SageMath function to compute invariants
def compute_invariants(a, b):
    try:
        E = EllipticCurve(QQ, [0, 0, 0, a, b])
        rank = -1
        try:
            E.two_descent(second_limit=13, verbose=False)
            rank = len(E.gens())
        except:
            try:
                points = E.points(bound=300)
                non_torsion = [p for p in points if p.order() == 0]
                rank = max(1, len(non_torsion)) if non_torsion else 0
            except:
                rank = E.rank(only_use_mwrank=False) if E.rank(only_use_mwrank=False) is not None else 0
        selmer_2 = E.selmer_rank()
        selmer_3_success = 1
        try:
            E.selmer_group(3, [])
        except:
            selmer_3_success = 0
        conductor = E.conductor()
        L = E.lseries()
        L1 = L.dokchitser(prec=50)(1)
        if abs(L1) < 1e-10:
            L1 = L.dokchitser(prec=50).derivative(1, 1)
        scaled_density = L1 * (1000 ** 0.5)
        return {'rank': rank, '2_selmer': selmer_2, '3_selmer_success': selmer_3_success,
                'conductor': conductor, 'L1': L1, 'scaled_density': scaled_density}
    except:
        return None

# Dataset
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

# Augment dataset
fib = generate_fibonacci(20)
new_data = []
for i in range(10, 19):
    a, b = fib[i], fib[i+1]
    invariants = compute_invariants(a, b)
    if invariants and invariants['rank'] >= 0:
        invariants.update({'a': a, 'b': b})
        new_data.append(invariants)
if new_data:
    df = pd.concat([df, pd.DataFrame(new_data)], ignore_index=True)
df['discriminant'] = -16 * (4 * df['a']**3 + 27 * df['b']**2)
df['a_b_ratio'] = df['a'] / df['b']
df['log_a'] = np.log1p(df['a'].abs())
df['log_b'] = np.log1p(df['b'].abs())
df = df[df['rank'] >= 0]
for target in ['rank', '2_selmer', '3_selmer_success']:
    df[target] = df[target].astype(int)

# Train predictors
X = df[['a', 'b', 'discriminant', 'a_b_ratio', 'log_a', 'log_b']]
targets = ['rank', '2_selmer', '3_selmer_success', 'conductor', 'L1', 'scaled_density']
models = {}
for target in targets:
    task = 'regression' if target in ['conductor', 'L1', 'scaled_density'] else 'classification'
    model = LGBMRegressor(min_child_samples=1) if task == 'regression' else LGBMClassifier(min_child_samples=1)
    model.fit(X, df[target])
    models[target] = model

# Optuna optimization
def objective(trial, X, y_dict):
    params = {
        'num_leaves': trial.suggest_int('num_leaves', 2, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'n_estimators': trial.suggest_int('n_estimators', 10, 50),
        'min_child_samples': 1
    }
    scores = []
    for target in ['rank', '2_selmer', '3_selmer_success', 'scaled_density']:
        y = y_dict[target]
        model = LGBMClassifier(**params) if target in ['rank', '2_selmer', '3_selmer_success'] else LGBMRegressor(**params)
        score = cross_val_score(
            model, X, y, cv=5,
            scoring='accuracy' if target in ['rank', '2_selmer', '3_selmer_success'] else 'neg_mean_squared_error'
        ).mean()
        scores.append(score if target in ['rank', '2_selmer', '3_selmer_success'] else -score / np.var(y))
    return -(2 * scores[0] + 1.5 * scores[1] + 1.5 * scores[2]) + scores[3]

optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction='minimize')
y_dict = {t: df[t] for t in targets}
study.optimize(lambda trial: objective(trial, X, y_dict), n_trials=100)
print(f"Best trial: value={study.best_value}, params={study.best_params}")

# Symbolic regression
def symbolic_regressor(X, y):
    est = SymbolicRegressor(
        population_size=500,
        generations=20,
        function_set=('add', 'sub', 'mul', 'div', 'sqrt'),
        parsimony_coefficient=0.01
    )
    est.fit(X, y)
    return est

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
    predicted_rank = models['rank'].predict(X_new)[0]
    predicted_L1 = models['L1'].predict(X_new)[0]
    predicted_3_selmer = models['3_selmer_success'].predict(X_new)[0]
    a_new, b_new = a, b
    if predicted_rank < 2 or predicted_3_selmer < 0.5 or predicted_L1 * 31.6 < 5000:
        a_new = a * (1 + np.random.uniform(-0.1, 0.1))
        b_new = b * (1 + np.random.uniform(-0.1, 0.1))
        X_new['a'], X_new['b'] = a_new, b_new
        X_new['discriminant'] = -16 * (4 * a_new**3 + 27 * b_new**2)
        X_new['a_b_ratio'] = a_new / b_new
        X_new['log_a'], X_new['log_b'] = np.log1p(abs(a_new)), np.log1p(abs(b_new))
        predicted = {t: models[t].predict(X_new)[0] for t in targets}
    invariants = compute_invariants(a_new, b_new)
    if invariants and invariants['3_selmer_success'] == 1 and invariants['rank'] >= 2 and invariants['scaled_density'] >= 5000:
        print(f"Success: a={a_new}, b={b_new}, invariants={invariants}")
        break