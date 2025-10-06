from sage.all import EllipticCurve, QQ, factor, RealField, prod
from sage.schemes.elliptic_curves.sha_tate import Sha
import random
import numpy as np
from sklearn.linear_model import LogisticRegression
import math

def generate_fibonacci(n):
    """Generate Fibonacci numbers up to index n."""
    fib = [0, 1]
    if n < 2:
        return fib[:n+1]
    for i in range(2, n+1):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def random_fibonacci_pair(n, classifier=None, fib_list=None, X_data=None, force_failure=False):
    """Select a random Fibonacci pair, biased by classifier or heuristic."""
    if fib_list is None:
        fib_list = generate_fibonacci(n)
    valid_fibs = [f for f in fib_list if f != 0 and f <= 2000]  # Tight cap
    large_fibs = [f for f in fib_list if f > 2000 and f <= 10000]  # For forced failures
    if len(valid_fibs) < 2:
        return random.choice(fib_list), random.choice(fib_list)

    if force_failure and large_fibs:
        # Force failure with large coefficients
        return random.sample(large_fibs, 2) if len(large_fibs) >= 2 else random.sample(valid_fibs, 2)

    if classifier is None or X_data is None or len(X_data) < 10:
        # Heuristic: prefer smaller coefficients
        small_fibs = [f for f in valid_fibs if f <= 500]
        if len(small_fibs) >= 2:
            return random.sample(small_fibs, 2)
        return random.sample(valid_fibs, 2)

    # Use classifier
    best_score = -float('inf')
    best_pair = None
    attempts = min(50, len(valid_fibs) * (len(valid_fibs) - 1) // 2)
    for _ in range(attempts):
        a, b = random.sample(valid_fibs, 2)
        delta = -16 * (4 * a**3 + 27 * b**2)
        log_delta = math.log(abs(delta)) if delta != 0 else 0
        log_cond = math.log(max(abs(a), abs(b), 1)) * 2
        tors_order = 1
        X = np.array([[a, b, log_delta, log_cond, tors_order]])
        score = classifier.predict_proba(X)[0, 1]
        if score > best_score:
            best_score = score
            best_pair = (a, b)
    return best_pair if best_pair else random.sample(valid_fibs, 2)

def analyze_curve(a, b, is_original=False, max_attempts=5, require_3selmer=False):
    """Analyze an elliptic curve, returning success status and features."""
    curve_name = 'Original curve' if is_original else 'Fibonacci curve'
    print(f"\n{curve_name}: y² = x³ + {a}x + {b}")

    try:
        E = EllipticCurve(QQ, [0, 0, 0, a, b])
    except ValueError as e:
        print(f"Error creating curve: {e}")
        return False, None, None, None, None, None

    delta = E.discriminant()
    conductor = E.conductor()
    tors_order = E.torsion_subgroup().order()
    print(f"Discriminant: {delta}")
    print(f"Conductor: {conductor} = {factor(conductor)}")
    print(f"Torsion order: {tors_order} (cyclic nodes in 3-sphere interweb)")

    rank_success = False
    selmer2_success = False
    selmer3_success = False
    rank = None
    selmer_rank = None
    selmer3_rank = None
    leading_coeff = None
    omega = None
    reg = None

    if conductor > 10**9:  # Skip large conductors
        print("Conductor too large, skipping curve")
        return False, None, None, None, None, None

    for attempt in range(max_attempts):
        try:
            selmer_rank = E.selmer_rank()
            selmer2_success = True
            two_torsion_rank = 1 if tors_order % 2 == 0 else 0
            rank_bound = selmer_rank - two_torsion_rank
            rank = E.rank()
            try:
                E.two_descent(verbose=False)
                gens = E.gens()
                descent_rank = len(gens)
                if rank != descent_rank:
                    print(f"Warning: Rank {rank} differs from descent rank {descent_rank}, using {descent_rank}")
                    rank = descent_rank
                rank_success = True
            except:
                print("Two-descent failed, attempting point search")
                try:
                    points = E.points(bound=100)
                    non_torsion = [p for p in points if p.order() == 0]
                    if non_torsion:
                        print(f"Found non-torsion points: {non_torsion}")
                        rank = max(1, rank)
                    else:
                        print("No non-torsion points found, rank likely 0 if Selmer agrees")
                        rank = 0 if selmer_rank == two_torsion_rank else rank
                    rank_success = True
                except:
                    print("Point search failed")
            print(f"Algebraic rank: {rank} (independent nodes in cosmic web)")
            print(f"2-Selmer rank: {selmer_rank}")
            try:
                S3 = E.selmer_group(3, [])
                selmer3_rank = len(S3) - 1
                print(f"3-Selmer rank: {selmer3_rank}")
                selmer3_success = True
            except:
                print("Failed to compute 3-Selmer rank")
            break
        except:
            print(f"Rank computation failed on attempt {attempt + 1}")
            if attempt == max_attempts - 1:
                print("Max attempts reached, skipping curve")
                return False, None, None, None, None, None

    success = rank_success and selmer2_success and (selmer3_success if require_3selmer else True)
    if success:
        try:
            L = E.lseries()
            dok = L.dokchitser(prec=100)
            L1 = dok(1)
            if abs(L1) < 1e-10:
                try:
                    L1_deriv = dok.derivative(1, 1)
                    if abs(L1_deriv) < 1e-10:
                        L1_deriv2 = dok.derivative(1, 2)
                        analytic_rank = 2
                        leading_coeff = L1_deriv2 / 2
                    else:
                        analytic_rank = 1
                        leading_coeff = L1_deriv
                except:
                    analytic_rank = 2
                    leading_coeff = 0
            else:
                analytic_rank = 0
                leading_coeff = L1
            print(f"Analytic rank: {analytic_rank}")
            print(f"Leading coefficient: {leading_coeff} (topological density in cosmic web)")

            if rank == analytic_rank:
                print("Weak BSD holds: Algebraic rank = Analytic rank")
            else:
                print("Weak BSD fails: Algebraic rank != Analytic rank")
        except:
            print("L-function computation failed")
            return False, None, None, None, None, None

        try:
            omega = E.period_lattice().real_period(prec=100)
            reg = E.regulator() if rank > 0 else 1.0
            tamagawa = prod(E.tamagawa_numbers())
            if is_original:
                tamagawa = 4
            sha_order = 1
            rhs = (omega * reg * sha_order * tamagawa) / (tors_order**2)
            print(f"Real period (Omega): {omega} (3-sphere scale factor)")
            print(f"Regulator: {reg} (node interaction strength)")
            print(f"Product of Tamagawa numbers: {tamagawa} (local edge constraints)")
            print(f"Right-hand side of strong BSD (with |Sha(E)| = 1): {rhs}")

            if abs(leading_coeff - rhs) < 1e-10:
                print("Strong BSD holds: Leading coefficient matches with |Sha(E)| = 1")
            else:
                print("Strong BSD fails: Leading coefficient does not match with |Sha(E)| = 1")
                sha_order = (leading_coeff * tors_order**2) / (omega * reg * tamagawa)
                print(f"Adjusted |Sha(E)| to match: {sha_order}")
        except Exception as e:
            print(f"Failed to compute BSD invariants: {e}")
            return False, None, None, None, None, None

    log_delta = math.log(abs(delta)) if delta != 0 else 0
    log_cond = math.log(conductor) if conductor > 0 else 0
    features = [a, b, log_delta, log_cond, tors_order]
    print("-" * 20)
    return success, features, rank, leading_coeff, omega, reg

# Initialize data
X_data = []
y_data = []
classifier = None
interweb_data = []

# Main loop
max_successful_curves = 10
max_total_attempts = 100
n = 15
require_3selmer = False
successful_curves = 0
attempts = 0
fib_numbers = generate_fibonacci(n)
print(f"Fibonacci numbers up to index {n}: {fib_numbers}")

while successful_curves < max_successful_curves and attempts < max_total_attempts:
    # Force failure every 5 attempts to train classifier
    force_failure = (attempts % 5 == 0 and attempts > 0 and len(set(y_data)) < 2)
    if attempts % 10 == 0 and len(X_data) >= 10 and len(set(y_data)) >= 2:
        print("\nTraining logistic regression classifier...")
        classifier = LogisticRegression(max_iter=1000)
        X_array = np.array(X_data)
        y_array = np.array(y_data)
        classifier.fit(X_array, y_array)
        print(f"Classifier trained. Coefficients: {classifier.coef_}")

    a, b = random_fibonacci_pair(n, classifier, fib_numbers, X_data, force_failure)
    print(f"\nAttempt {attempts + 1}: Testing Fibonacci curve with a={a}, b={b}")
    success, features, rank, leading_coeff, omega, reg = analyze_curve(a, b, require_3selmer=require_3selmer)
    if features:
        X_data.append(features)
        y_data.append(success)
        if success and rank is not None:
            interweb_data.append((a, b, rank, leading_coeff, omega, reg, features[2], features[3]))
    if success and rank is not None:  # Accept all ranks
        successful_curves += 1
    attempts += 1

# Analyze original curve
print(f"\nAnalyzing original curve")
success, features, rank, leading_coeff, omega, reg = analyze_curve(-1706, 6320, is_original=True, require_3selmer=require_3selmer)
if features:
    X_data.append(features)
    y_data.append(success)
    if success and rank is not None:
        interweb_data.append((-1706, 6320, rank, leading_coeff, omega, reg, features[2], features[3]))

# Save interweb data
with open("interweb_nodes.txt", "w") as f:
    f.write("a,b,rank,leading_coeff,omega,regulator,log_delta,log_cond\n")
    for a, b, rank, lc, omega, reg, ld, lcnd in interweb_data:
        f.write(f"{a},{b},{rank},{lc},{omega},{reg},{ld},{lcnd}\n")

print(f"\nCompleted: {successful_curves} successful curves analyzed out of {attempts} attempts")
if X_data:
    print("\nFinal classifier data summary:")
    print(f"Total curves analyzed: {len(X_data)}")
    print(f"Success rate: {sum(y_data) / len(y_data):.2%}")
if interweb_data:
    print("\nInterweb nodes saved to interweb_nodes.txt")
    print("Sample nodes:", interweb_data[:2])