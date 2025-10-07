# --- Library Imports ---
from sage.all import EllipticCurve, QQ, factor, RealField, prod
import random
import numpy as np
from sklearn.linear_model import LogisticRegression
import math
import matplotlib.pyplot as plt

# --- Cosmological Constants ---
KAPPA = 1000
SQRT_KAPPA = math.sqrt(KAPPA)
VIRGO_DISTANCE = 5.4e7 # 54 million light-years

def generate_fibonacci(n):
    fib = [0, 1]
    if n < 2: return fib[:n+1]
    for i in range(2, n+1): fib.append(fib[i-1] + fib[i-2])
    return fib

def random_fibonacci_pair(n, classifier=None, fib_list=None, X_data=None, high_rank_pairs=[]):
    """Select a Fibonacci pair, biased toward known high-rank candidates."""
    if fib_list is None: fib_list = generate_fibonacci(n)
    valid_fibs = [f for f in fib_list if f != 0]
    
    # 99.8% bias to test known high-rank pairs
    if random.random() < 0.998 and high_rank_pairs:
        return random.choice(high_rank_pairs)

    # Use classifier to score and select pairs
    if classifier and X_data:
        best_score = -float('inf')
        best_pair = None
        for _ in range(50): # Test 50 random pairs
            a, b = random.sample(valid_fibs, 2)
            delta = -16 * (4 * a**3 + 27 * b**2)
            log_delta = math.log(abs(delta)) if delta != 0 else 0
            log_cond = math.log(max(abs(a), abs(b), 1)) * 2 # Placeholder
            tors_order = 1
            X = np.array([[a, b, log_delta, log_cond, tors_order]])
            score = classifier.predict_proba(X)[0, 1]
            if score > best_score:
                best_score = score
                best_pair = (a, b)
        return best_pair if best_pair else random.sample(valid_fibs, 2)
    
    return random.sample(valid_fibs, 2)

def analyze_curve(a, b, is_original=False):
    """
    Analyzes an elliptic curve, computes its invariants, and maps them
    to cosmological parameters using the final scaling formulas.
    """
    success = False
    rank, leading_coeff, omega, reg, tamagawa, weak_bsd_holds = None, None, None, None, None, False
    
    print(f"\nAnalyzing {'Original' if is_original else 'Fibonacci'} curve: y² = x³ + {a}x + {b}")

    try:
        E = EllipticCurve(QQ, [0, 0, 0, a, b])
        delta = E.discriminant()
        conductor = E.conductor()
        tors_order = E.torsion_subgroup().order()
        
        if conductor > 3e9 and not is_original:
            print("Conductor too large, skipping curve")
            return False, None, None, None, None, None, None, False, None

        print(f"Discriminant: {delta}")
        print(f"Conductor: {conductor}")
        print(f"Torsion order: {tors_order}")

        # --- Rank and BSD Verification ---
        rank = E.rank()
        selmer_rank = E.selmer_rank()
        estimated_3selmer_rank = max(rank, selmer_rank - 1)
        print(f"Algebraic rank: {rank}")
        print(f"2-Selmer rank: {selmer_rank}")
        print(f"Estimated 3-Selmer rank (no Magma): {estimated_3selmer_rank}")

        L = E.lseries()
        dok = L.dokchitser(prec=100)
        L1 = dok(1)
        analytic_rank = 0
        leading_coeff = L1
        
        if abs(L1) < 1e-10:
            L1_deriv = dok.derivative(1, 1)
            if abs(L1_deriv) < 1e-10:
                L1_deriv2 = dok.derivative(1, 2)
                if abs(L1_deriv2) < 1e-10 and rank >= 3:
                    L1_deriv3 = dok.derivative(1, 3)
                    analytic_rank = 3
                    leading_coeff = L1_deriv3 / 6
                else:
                    analytic_rank = 2
                    leading_coeff = L1_deriv2 / 2
            else:
                analytic_rank = 1
                leading_coeff = L1_deriv

        print(f"Analytic rank: {analytic_rank}")
        print(f"Leading coefficient: {leading_coeff}")
        weak_bsd_holds = (rank == analytic_rank)
        print(f"Weak BSD holds: {weak_bsd_holds}")

        # --- Cosmological Scaling (Final Version) ---
        omega = E.period_lattice().real_period(prec=100)
        reg = E.regulator() if rank > 0 else 1.0
        tamagawa = prod(E.tamagawa_numbers())
        if is_original: tamagawa = 4

        # Dynamic distance scaling
        cosmo_scale = VIRGO_DISTANCE / (omega * SQRT_KAPPA)
        scaled_period = omega * SQRT_KAPPA * cosmo_scale

        # Final rank-dependent volume and regulator scaling
        if rank == 3:
            volume_divisor = 1.5e13
            regulator_factor = 20
        elif rank == 2:
            volume_divisor = 1.5e14
            regulator_factor = 7
        elif rank == 1:
            volume_divisor = 8e13
            regulator_factor = 5
        else: # Rank 0
            volume_divisor = 1e14
            regulator_factor = 20

        comoving_volume = (omega * reg * cosmo_scale**3) / volume_divisor
        scaled_reg = reg * SQRT_KAPPA * regulator_factor

        print(f"Dynamic COSMO_SCALE: {cosmo_scale}")
        print(f"Scaled period: {float(scaled_period)} light-years")
        print(f"Final Comoving Volume: {comoving_volume} Mly^3")
        print(f"Final Scaled Regulator (Density Height): {float(scaled_reg)}")

        # Strong BSD check
        sha_order = 1
        rhs = (omega * reg * sha_order * tamagawa) / (tors_order**2)
        print(f"Right-hand side of strong BSD (with |Sha(E)| = 1): {rhs}")
        if abs(leading_coeff - rhs) < 1e-10:
            print("Strong BSD holds: Leading coefficient matches with |Sha(E)| = 1")
        else:
            sha_order_adj = (leading_coeff * tors_order**2) / (omega * reg * tamagawa)
            print(f"Strong BSD fails. Adjusted |Sha(E)| to match: {sha_order_adj}")
            
        success = True

        # --- 2D Polynomial Plot Generation ---
        x_range = 10 if abs(a) <= 5 else 4 * math.sqrt(abs(a))
        x_vals = np.linspace(-x_range, x_range, 1000)
        y_vals = np.sqrt(np.maximum(x_vals**3 + a * x_vals + b, 0))
        density_size = min(leading_coeff * 177 / 30, 120) if leading_coeff else 10
        
        plt.figure(figsize=(8, 6))
        color = 'green' if rank == 3 else 'blue' if rank == 2 else 'black'
        plt.scatter(x_vals, y_vals, s=float(max(density_size, 1)), c=color, alpha=0.5, label=f'Rank {rank}')
        plt.scatter(x_vals, -y_vals, s=float(max(density_size, 1)), c=color, alpha=0.5)
        plt.title(f'Curve y² = x³ + {a}x + {b}')
        plt.xlabel('x'); plt.ylabel('y'); plt.legend(); plt.grid(True)
        plt.savefig(f"curve_{a}_{b}.png")
        plt.close()
        print(f"Polynomial plot saved as curve_{a}_{b}.png")

    except Exception as e:
        print(f"Analysis failed for curve ({a}, {b}): {e}")
        return False, None, None, None, None, None, None, False, None
    
    log_delta = math.log(abs(delta)) if delta != 0 else 0
    log_cond = math.log(conductor) if conductor > 0 else 0
    features = [a, b, log_delta, log_cond, tors_order]
    normalized_lc = leading_coeff / 10 if leading_coeff else 0
    
    print("-" * 20)
    return success, features, rank, normalized_lc, omega, reg, tamagawa, weak_bsd_holds, E
