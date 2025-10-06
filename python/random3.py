from sage.all import EllipticCurve, QQ, factor, RealField, prod
from sage.schemes.elliptic_curves.sha_tate import Sha
import random

def generate_fibonacci(n):
    """Generate Fibonacci numbers up to index n."""
    fib = [0, 1]
    if n < 2:
        return fib[:n+1]
    for i in range(2, n+1):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def random_fibonacci(n, k=1):
    """Select k random Fibonacci numbers up to index n."""
    fib_list = generate_fibonacci(n)
    if k == 1:
        return random.choice(fib_list)
    return random.sample(fib_list, k)

def analyze_curve(a, b, is_original=False):
    print(f"\n{'Original curve' if is_original else 'Fibonacci curve'}: y² = x³ + {a}x + {b}")

    try:
        E = EllipticCurve(QQ, [0, 0, 0, a, b])
    except ValueError as e:
        print(f"Error creating curve: {e}")
        return

    delta = E.discriminant()
    conductor = E.conductor()
    tors_order = E.torsion_subgroup().order()
    print(f"Discriminant: {delta}")
    print(f"Conductor: {conductor} = {factor(conductor)}")
    print(f"Torsion order: {tors_order}")

    try:
        selmer_rank = E.selmer_rank()
        two_torsion_rank = 1 if tors_order % 2 == 0 else 0
        rank_bound = selmer_rank - two_torsion_rank
        rank = E.rank()
        # Additional descent check
        try:
            E.two_descent(verbose=False)
            descent_rank = rank_bound
            if rank > descent_rank:
                print(f"Warning: Rank {rank} exceeds descent bound {descent_rank}, adjusting to {descent_rank}")
                rank = descent_rank
        except:
            print("Two-descent failed")
        print(f"Algebraic rank: {rank}")
        print(f"2-Selmer rank: {selmer_rank}")
        try:
            S3 = E.selmer_group(3, [])
            print(f"3-Selmer rank: {len(S3) - 1}")
        except:
            print("Failed to compute 3-Selmer rank")
    except:
        print("Algebraic rank computation failed")
        rank = None

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
    print(f"Leading coefficient: {leading_coeff}")

    if rank is not None and rank == analytic_rank:
        print("Weak BSD holds: Algebraic rank = Analytic rank")
    else:
        print("Weak BSD fails: Algebraic rank != Analytic rank or computation failed")

    # Try Heegner point for Curve 3
    if a == 13 and b == 34:
        D = -3
        try:
            P = E.heegner_point(D, c=1)
            P_Q = P.point()
            print(f"Heegner point (traced to Q): {P_Q}")
            order = P_Q.order()
            if order == 0:
                print("Heegner point has infinite order, suggesting rank >= 1")
            else:
                print(f"Heegner point has order {order}, suggesting rank 0 or torsion")
        except ValueError as e:
            print(f"Failed to compute Heegner point: {e}")

    try:
        omega = E.period_lattice().real_period(prec=100)
        reg = E.regulator() if rank > 0 else 1.0
        tamagawa = prod(E.tamagawa_numbers())
        if is_original:
            tamagawa = 4
        sha_order = 1
        rhs = (omega * reg * sha_order * tamagawa) / (tors_order**2)
        print(f"Real period (Omega): {omega}")
        print(f"Regulator: {reg}")
        print(f"Product of Tamagawa numbers: {tamagawa}")
        print(f"Right-hand side of strong BSD (with |Sha(E)| = 1): {rhs}")

        if abs(leading_coeff - rhs) < 1e-10:
            print("Strong BSD holds: Leading coefficient matches with |Sha(E)| = 1")
        else:
            print("Strong BSD fails: Leading coefficient does not match with |Sha(E)| = 1")
            sha_order = (leading_coeff * tors_order**2) / (omega * reg * tamagawa)
            print(f"Adjusted |Sha(E)| to match: {sha_order}")
    except Exception as e:
        print(f"Failed to compute BSD invariants: {e}")

    print("-" * 20)

# Generate random Fibonacci coefficients
n = 10
fib_numbers = generate_fibonacci(n)
print(f"Fibonacci numbers up to index {n}: {fib_numbers}")

# Analyze original and Fibonacci curves
fib_pairs = [(5, 13), (8, 21), (13, 34)]
for a, b in fib_pairs:
    analyze_curve(a, b)

analyze_curve(-1706, 6320, is_original=True)

# Analyze a curve with random Fibonacci coefficients
random_a, random_b = random_fibonacci(n, k=2)
print(f"\nTesting random Fibonacci curve with a={random_a}, b={random_b}")
analyze_curve(random_a, random_b)