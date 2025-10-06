from sage.all import EllipticCurve, QQ, factor, RealField
from sage.schemes.elliptic_curves.sha_tate import Sha

def analyze_curve(a, b, is_original=False):
    print(f"\n{'Original curve' if is_original else 'Fibonacci curve'}: y² = x³ + {a}x + {b}")

    # Define the elliptic curve
    try:
        E = EllipticCurve(QQ, [0, 0, 0, a, b])
    except ValueError as e:
        print(f"Error creating curve: {e}")
        return

    # Compute basic invariants
    delta = E.discriminant()
    conductor = factor(E.conductor())
    tors_order = E.torsion_subgroup().order()
    print(f"Discriminant: {delta}")
    print(f"Conductor: {conductor}")
    print(f"Torsion order: {tors_order}")

    # Compute algebraic rank carefully
    try:
        rank = E.rank()
        print(f"Algebraic rank: {rank}")
    except:
        print("Algebraic rank computation failed")
        rank = None

    # Compute analytic rank and leading coefficient
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

    # Verify weak BSD
    if rank is not None and rank == analytic_rank:
        print("Weak BSD holds: Algebraic rank = Analytic rank")
    else:
        print("Weak BSD fails: Algebraic rank != Analytic rank or computation failed")

    # Compute Heegner points
    D = -19  # Quadratic imaginary field Q(sqrt(-19))
    try:
        P = E.heegner_point(D, c=1)  # Heegner point with conductor 1
        P_Q = P.point()  # Trace to E(Q)
        print(f"Heegner point (traced to Q): {P_Q}")
        order = P_Q.order()
        if order == 0:
            print("Heegner point has infinite order, suggesting rank >= 1")
        else:
            print(f"Heegner point has order {order}, suggesting rank 0 or torsion")
    except ValueError as e:
        print(f"Failed to compute Heegner point: {e}")

    # Compute 2-Selmer rank
    try:
        selmer_rank = E.selmer_rank()
        two_torsion_rank = 1 if tors_order % 2 == 0 else 0
        sha_two_rank = selmer_rank - rank - two_torsion_rank if rank is not None else None
        print(f"2-Selmer rank: {selmer_rank}")
        print(f"Rank of Sha(E)[2]: {sha_two_rank}")
        if sha_two_rank == 0:
            print("Sha(E)[2] = 0, suggesting |Sha(E)| is odd or 1")
        elif sha_two_rank is not None:
            print(f"|Sha(E)[2]| = 2^{sha_two_rank}")
    except:
        print("Failed to compute 2-Selmer rank")

    # Compute BSD invariants for strong BSD
    try:
        omega = E.period_lattice().real_period(prec=100)
        reg = E.regulator() if rank > 0 else 1.0
        tamagawa = prod(E.tamagawa_numbers())
        sha_order = 1  # Initial hypothesis
        rhs = (omega * reg * sha_order * tamagawa) / (tors_order**2)
        print(f"Real period (Omega): {omega}")
        print(f"Regulator: {reg}")
        print(f"Product of Tamagawa numbers: {tamagawa}")
        print(f"Right-hand side of strong BSD (with |Sha(E)| = 1): {rhs}")

        # Verify strong BSD
        if abs(leading_coeff - rhs) < 1e-10:
            print("Strong BSD holds: Leading coefficient matches with |Sha(E)| = 1")
        else:
            print("Strong BSD fails: Leading coefficient does not match with |Sha(E)| = 1")
            sha_order = (leading_coeff * tors_order**2) / (omega * reg * tamagawa)
            print(f"Adjusted |Sha(E)| to match: {sha_order}")
    except:
        print("Failed to compute BSD invariants")

    print("-" * 20)

# Example calls
fib_pairs = [(5, 13), (8, 21), (13, 34)]
for a, b in fib_pairs:
    analyze_curve(a, b)

analyze_curve(-1706, 6320, is_original=True)