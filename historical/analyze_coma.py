import pandas as pd
import numpy as np
from sage.all import EllipticCurve, QQ, factor, pari, prod
pari.allocatemem(8589934592)
from sage.parallel.decorate import parallel

# Predicted curve for Coma
E_coma = EllipticCurve(QQ, [-10141, 9980]) 
CURVE_COMA_NAME = "Coma Cluster Predicted Curve"

# Calculate the discriminant of the curve E_coma
delta = E_coma.discriminant()
print(f"Discriminant Delta: {delta}")

# Compute the torsion subgroup of E_coma
torsion_subgroup = E_coma.torsion_subgroup()
print(f"Torsion Subgroup: {torsion_subgroup}")

# Compute the algebraic rank of E_coma
algebraic_rank = E_coma.rank()
print(f"Algebraic Rank: {algebraic_rank}")

# Find the generator(s) of the free part of the Mordell-Weil group
generators = E_coma.gens()
print(f"Generators: {generators}")

# Compute the L-series associated with E_coma
L = E_coma.lseries()

# Compute the value of L(E,s) at s=1
L_value_at_1 = L(1)
print(f"L(E, 1): {L_value_at_1}")

# Compute the value of the first derivative L'(E,s) at s=1
L_derivative_at_1 = L.dokchitser().derivative(1, 1)
print(f"L'(E, 1) (Standard Precision): {L_derivative_at_1}")

# Re-compute L'(E,1) with higher precision
L_derivative_high_precision = E_coma.lseries().dokchitser(prec=100).derivative(1, 1)
print(f"L'(E, 1) (High Precision): {L_derivative_high_precision}")

# Compute the real period with higher precision
omega_high_precision = E_coma.period_lattice().real_period(prec=100)
print(f"Real Period (Omega): {omega_high_precision}")

# Compute the regulator with higher precision
if generators:
    P = E_coma.gens()[0]
    regulator_high_precision = P.height(precision=100)
    print(f"Regulator (Height of P): {regulator_high_precision}")
else:
    regulator_high_precision = 1
    print(f"Regulator: {regulator_high_precision} (Rank 0 curve)")

# Compute the product of the Tamagawa numbers
tamagawa_product = prod(E_coma.tamagawa_numbers())
print(f"Product of Tamagawa Numbers: {tamagawa_product}")

# Perform a verbose 2-descent to analyze the 2-Selmer group
print("\nInitiating Verbose 2-Descent on E_coma:")
E_coma.two_descent(verbose=True)
print("\n2-Descent complete.")

def analyze_3_selmer_evidence(E, curve_name):
    """
    Performs a multi-pronged analysis of an elliptic curve to build a case
    for its 3-Selmer rank without relying on Magma. It checks standard algebraic,
    2-Selmer (upper bound), and analytic ranks for convergence.

    Args:
        E (EllipticCurve): The SageMath elliptic curve object to analyze.
        curve_name (str): The common name or coefficients of the curve for logging.

    Returns:
        dict: A dictionary containing the results from each analytical step.
    """
    print("="*60)
    print(f"Analyzing Curve: {curve_name}")
    print(f"Equation: {E}")
    print("="*60)

    results = {
        'curve_name': curve_name,
        'equation': str(E),
        'evidence': {}
    }

    # --- 1. Baseline: Standard SageMath Rank (Algebraic) ---
    # This uses Sage's default (often PARI-based) methods for 2-descent.
    try:
        # NOTE: This method can be slow or fail for curves with very high regulators.
        rank = E.rank()
        results['evidence']['sage_algebraic_rank'] = rank
        print(f"[Step 1] SageMath Algebraic Rank (Best Effort): {rank}")
    except Exception as e:
        print(f"[Step 1] SageMath Rank computation failed: {e}")
        results['evidence']['sage_algebraic_rank'] = 'Error'

    # --- 2. PARI/GP Backend: 2-Selmer Rank (Upper Bound) ---
    # The 2-Selmer rank is a robust upper bound for the true rank.
    try:
        # Use the PARI interface directly for a robust check
        pari_E = pari(E)
        # ellrank() returns [rank, 2-Selmer rank, ...]. We want the 2-Selmer rank.
        selmer_2_rank = pari_E.ellrank()[1]
        results['evidence']['pari_2_selmer_rank'] = int(selmer_2_rank)
        print(f"[Step 2] PARI/GP 2-Selmer Rank (Upper Bound): {selmer_2_rank}")
    except Exception as e:
        print(f"[Step 2] PARI/GP 2-Selmer computation failed: {e}")
        results['evidence']['pari_2_selmer_rank'] = 'Error'

    # --- 3. PARI/GP Backend: Analytic Rank (via BSD Conjecture) ---
    # The analytic rank should equal the algebraic rank if BSD holds.
    try:
        analytic_rank_info = pari(E).ellanalyticrank()
        # ellanalyticrank() returns [rank, L(1), L'(1), ...]. We want the rank.
        analytic_rank = int(analytic_rank_info[0])
        results['evidence']['pari_analytic_rank'] = analytic_rank
        print(f"[Step 3] PARI/GP Analytic Rank (via BSD): {analytic_rank}")
    except Exception as e:
        print(f"[Step 3] PARI/GP Analytic Rank computation failed: {e}")
        results['evidence']['pari_analytic_rank'] = 'Error'
        
    # --- 4. 3-Torsion Analysis ---
    # The presence of rational 3-torsion points can influence the 3-Selmer group.
    try:
        torsion_subgroup = E.torsion_subgroup()
        torsion_order = torsion_subgroup.order()
        has_3_torsion = (torsion_order % 3 == 0)
        results['evidence']['has_rational_3_torsion'] = has_3_torsion
        print(f"[Step 4] Rational 3-Torsion Points Present: {has_3_torsion} (Torsion Order: {torsion_order})")
    except Exception as e:
        print(f"[Step 4] Torsion analysis failed: {e}")
        results['evidence']['has_rational_3_torsion'] = 'Error'

    # --- 5. The 3-Selmer Proxy: Convergent Rank Inference ---
    # We infer a lower bound for the 3-Selmer rank based on the convergence of the
    # algebraic, analytic, and 2-Selmer ranks.
    print("\n[Step 5] Inferring 3-Selmer Rank Lower Bound (Magma-free proxy)...")
    try:
        # Collect only successfully computed integer ranks
        rank_evidence = [r for r in [
            results['evidence'].get('sage_algebraic_rank'),
            results['evidence'].get('pari_2_selmer_rank'),
            results['evidence'].get('pari_analytic_rank')
        ] if isinstance(r, int)]

        if rank_evidence:
            min_rank = min(rank_evidence)
            max_rank = max(rank_evidence)

            if min_rank == max_rank:
                convergent_rank = min_rank
                # Inference: If the ranks agree, the true rank is likely this value.
                # Since Sel_3(E) contains the rational points, its dimension must be >= rank(E).
                estimated_3_selmer_bound = convergent_rank
                results['evidence']['estimated_3_selmer_bound'] = estimated_3_selmer_bound
                print(f"  > All rank indicators converge to {convergent_rank}.")
                print(f"  > Strong evidence for a 3-Selmer Rank $\\ge$ {estimated_3_selmer_bound}.")
            else:
                results['evidence']['estimated_3_selmer_bound'] = f'Inconsistent: min={min_rank}, max={max_rank}'
                print("  > Rank indicators are inconsistent; 3-Selmer bound is inconclusive.")
        else:
            results['evidence']['estimated_3_selmer_bound'] = 'Inconclusive'
            print("  > Rank indicators are inconclusive (all failed or returned non-integer).")

    except Exception as e:
        print(f"[Step 5] 3-Selmer proxy analysis failed: {e}")
        results['evidence']['estimated_3_selmer_bound'] = 'Error'

    # --- Final Conclusion ---
    final_estimate = results['evidence'].get('estimated_3_selmer_bound')
    results['final_conclusion'] = final_estimate
    print("\n--- Conclusion ---")
    if isinstance(final_estimate, int):
        print(f"The convergent evidence suggests a 3-Selmer Rank of at least {final_estimate}.")
        print(f"This is the predicted rank of the curve $E_{{{curve_name}}}$.")
    else:
        print(f"The evidence is inconclusive. Further analysis is required.")
        
    print("="*60 + "\n")
    return results

if __name__ == '__main__':
    # --- Define the Target Curves for Analysis ---
    
    # 1. The Coma Cluster Curve (The primary target)
    curve_coma = E_coma
    
    # 2. Cornerstone Rank 3 curve from your research ("Synthesis" paper)
    curve_3salmer_candidate = EllipticCurve(QQ, [0, 0, 0, 2, 144])

    # 3. The original Virgo curve (Rank 1 case)
    curve_virgo = EllipticCurve(QQ, [0, 0, 0, -1706, 6320])

    # --- Run the Analysis Pipeline ---
    all_results = []
    
    # Run the user's primary curve first
    all_results.append(analyze_3_selmer_evidence(curve_coma, CURVE_COMA_NAME))
    
    # Run comparison curves
    all_results.append(analyze_3_selmer_evidence(curve_3salmer_candidate, "Rank 3 Analogue: $y^2 = x^3 + 2x + 144$"))
    all_results.append(analyze_3_selmer_evidence(curve_virgo, "Virgo Cluster (Rank 1 Analogue)"))

    # --- Print Final Summary ---
    print("\n\n" + "="*80)
    print("                      FINAL 3-SELMER ANALYSIS SUMMARY")
    print("="*80)
    for res in all_results:
        print(f"\nCurve: {res['curve_name']}")
        print(f"  > Equation: {res['equation']}")
        print(f"  > Algebraic Rank (Sage): {res['evidence'].get('sage_algebraic_rank', 'N/A')}")
        print(f"  > Analytic Rank (PARI): {res['evidence'].get('pari_analytic_rank', 'N/A')}")
        print(f"  > Final Estimated 3-Selmer Rank (Lower Bound): {res['final_conclusion']}")
