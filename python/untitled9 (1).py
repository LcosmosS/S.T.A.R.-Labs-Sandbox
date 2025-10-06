import optuna
from sage.all import 
from cypari2 import Pari*
from cypari2 import Pari

pari.allocatemem(10**9)  # Allocate 1GB



def objective(trial):
    i = trial.suggest_int('i', 1, 15)  # Smaller range
    j = trial.suggest_int('j', 1, 15)
    a = fibonacci(i)
    b = fibonacci(j)
    
    try:
        E = EllipticCurve([0, 0, 0, a, b])
        
        # Compute rank with fallback
        try:
            rank = E.rank()
        except Exception:
            try:
                E.two_descent(second_limit=13)
                rank = len(E.gens())
            except:
                rank = 0
        
        # 2-Selmer rank
        try:
            selmer_2 = E.selmer_rank()
            selmer_2_success = True
        except:
            selmer_2 = 0
            selmer_2_success = False
        
        # 3-Selmer group (optional success)
        try:
            selmer_3_group = E.selmer_group(3)
            selmer_3_success = True
        except:
            selmer_3_success = False
        
        # Conductor
        conductor = E.conductor()
        
        # Scoring
        if rank >= 2 and selmer_2_success:  # Relaxed 3-Selmer requirement
            score = rank
        else:
            score = -10
        
        # Optional conductor penalty
        # target_conductor = 2353320476
        # conductor_penalty = 0.0001 * abs(conductor - target_conductor)
        # score -= conductor_penalty
        
        print(f"Trial {trial.number}: i={i}, j={j}, a={a}, b={b}, rank={rank}, "
              f"selmer_2_success={selmer_2_success}, selmer_3_success={selmer_3_success}, "
              f"conductor={conductor}, score={score}")
        
        return -score  # Optuna minimizes, so negate score
    except ArithmeticError:
        return 0

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=100)

best_trial = study.best_trial
print(f"\nBest trial parameters: {best_trial.params}")
print(f"Best score (rank): {-best_trial.value}")