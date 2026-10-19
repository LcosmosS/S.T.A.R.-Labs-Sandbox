# Define the Fibonacci function
def fibonacci(n):
    if n < 0:
        raise ValueError("Fibonacci sequence not defined for negative indices")
    if n == 0:
        return 0
    if n == 1:
        return 1
    fib = [0, 1]
    for i in range(2, n + 1):
        fib.append(fib[i-1] + fib[i-2])
    return fib[n]

# Define the pairs of indices
pairs = [(5, 7), (6, 8), (7, 9)]

# Loop over each pair to construct and analyze the curve
for n1, n2 in pairs:
    a = fibonacci(n1)
    b = fibonacci(n2)
    print(f"\nCurve with a = F_{n1} = {a}, b = F_{n2} = {b}: y^2 = x^3 + {a}x + {b}")

    # Define the elliptic curve
    E = EllipticCurve(QQ, [a, b])

    # Compute the discriminant
    delta = E.discriminant()
    print(f"Discriminant: {delta}")
    if delta == 0:
        print("Not an elliptic curve (singular). Skipping.")
        continue

    # Compute the conductor
    conductor = E.conductor()
    print(f"Conductor: {conductor}")

    # Compute the torsion subgroup
    tors = E.torsion_subgroup()
    tors_order = tors.order()
    print(f"Torsion subgroup order: {tors_order}")

    # Compute the rank
    rank = E.rank()
    print(f"Algebraic rank: {rank}")

    # Compute the L-function and analytic rank
    L = E.lseries()
    L_dok = L.dokchitser(prec=100)
    L1 = L_dok(1) # Evaluate L(1)
    if abs(L1) < 1e-10: # Check if L(1) is approximately 0
        L1_deriv = L_dok.derivative(1, 1) # Compute L'(1)
        if abs(L1_deriv) < 1e-10: # Check if L'(1) is approximately 0
            L1_deriv2 = L_dok.derivative(1, 2) # Compute L''(1)
            if abs(L1_deriv2) < 1e-10:
                analytic_rank = 3
                leading_coeff = L1_deriv2 / 2
            else:
                analytic_rank = 2
                leading_coeff = L1_deriv2 / 2
        else:
            analytic_rank = 1
            leading_coeff = L1_deriv
    else:
        analytic_rank = 0
        leading_coeff = L1
    print(f"Analytic rank: {analytic_rank}")
    print(f"Leading coefficient L^({analytic_rank})(E, 1): {leading_coeff}")

    # Verify weak BSD
    if rank == analytic_rank:
        print("Weak BSD holds: Algebraic rank = Analytic rank")
    else:
        print("Weak BSD fails: Algebraic rank != Analytic rank")

    # Compute BSD invariants for strong BSD
    omega = E.period_lattice().real_period(prec=100)
    # Compute the regulator, handling rank 0 case
    if rank == 0:
        reg = 1.0 # Regulator is 1 for rank 0
    else:
        reg = E.regulator()
    tamagawa = prod(E.tamagawa_numbers())
    sha_order = 1 # Initial hypothesis based on 2-Selmer rank

    # Compute the right-hand side of the strong BSD formula
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
        # Adjust Sha(E) to match
        sha_order_adj = (leading_coeff * tors_order**2) / (omega * reg * tamagawa)
        print(f"Adjusted |Sha(E)| to match: {sha_order_adj}")
