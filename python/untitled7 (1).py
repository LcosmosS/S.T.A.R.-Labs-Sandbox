import optuna
from sage.all import *

def objective(trial):
    """
    Define the objective function for Optuna to minimize.
    Returns a value to minimize; we use -score to maximize desirable properties.
    """
    # Suggest Fibonacci indices i and j between 1 and 20
    i = trial.suggest_int('i', 1, 20)
    j = trial.suggest_int('j', 1, 20)
    
    # Generate Fibonacci coefficients
    a = fibonacci(i)  # fibonacci(n) gives the nth Fibonacci number (1-based indexing here)
    b = fibonacci(j)
    
    try:
        # Define the elliptic curve y² = x³ + a*x + b
        E = EllipticCurve([0, 0, 0, a, b])
        
        # Compute rank
        try:
            rank = E.rank()
            rank_success = True
        except Exception:
            rank = 0
            rank_success = False
        
        # Compute 2-Selmer rank
        try:
            selmer_2 = E.selmer_rank()
            selmer_2_success = True
        except Exception:
            selmer_2 = 0
            selmer_2_success = False
        
        # Compute 3-Selmer group (success check only)
        try:
            selmer_3_group = E.selmer_group(3)
            selmer_3_success = True
        except Exception:
            selmer_3_success = False
        
        # Compute conductor
        conductor = E.conductor()
        
        # Define the score
        if rank_success and selmer_2_success and selmer_3_success and rank >= 2:
            score = rank  # Reward higher rank among qualifying curves
        else:
            score = -10   # Penalize curves that don't meet criteria
        
        # Optional: Adjust score based on conductor (uncomment and modify as needed)
        # target_conductor = 2353320476
        # conductor_penalty = 0.0001 * abs(conductor - target_conductor)
        # score -= conductor_penalty
        
        # Log trial details
        print(f"Trial {trial.number}: i={i}, j={j}, a={a}, b={b}, rank={rank}, "
              f"selmer_2_success={selmer_2_success}, selmer_3_success={selmer_3_success}, "
              f"conductor={conductor}, score={score}")
        
        return -score  # Optuna minimizes, so negate score to maximize it
    
    except ArithmeticError:  # Handle singular curves (discriminant = 0)
        return 0  # Assign neutral score to skip invalid curves

# Create and run the Optuna study
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=100)

# Retrieve and display the best trial
best_trial = study.best_trial
print(f"\nBest trial parameters: {best_trial.params}")
print(f"Best score (rank): {-best_trial.value}")  # Negate to show actual score