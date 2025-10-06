from sage.all import EllipticCurve, QQ, factor
from sage.schemes.elliptic_curves import sha_tate

def analyze_curve(a, b, is_original=False):
    print(f"\n{'Original curve' if is_original else 'Fibonacci curve'}: y² = x³ + {a}x + {b}")

    try:
        E = EllipticCurve(QQ, [a, b])
    except ValueError as e:
        print(f"Error creating curve: {e}")
        return

    print(f"Discriminant: {E.discriminant()}")
    print(f"Conductor: {factor(E.conductor())}")
    print(f"Torsion order: {E.torsion_order()}")

    try:
        rank = E.rank()
        print(f"Algebraic rank: {rank}")
    except:
        print("Algebraic rank computation failed")

    L = E.lseries()
    dok = L.dokchitser()
    L1 = dok(1)

    if abs(L1) < 1e-10:
        try:
            leading_coeff = dok.derivative(1, 1)
            analytic_rank = 1
        except:
            leading_coeff = 0
            analytic_rank = 2
    else:
        leading_coeff = L1
        analytic_rank = 0

    print(f"Analytic rank: {analytic_rank}")
    print(f"Leading coefficient: {leading_coeff:.5f}")

    try:
        P = E.heegner_point()
        print(f"Heegner Point: {P}")
    except:
        print("No Heegner output")

    try:
        two_descent = E.two_descent()
        print(two_descent)
    except:
        print("No two descent")

    print("-" * 20)

# Example calls
fib_pairs = [(5, 13), (8, 21), (13, 34)]
for a, b in fib_pairs:
    analyze_curve(a, b)

analyze_curve(-1706, 6320, is_original=True)