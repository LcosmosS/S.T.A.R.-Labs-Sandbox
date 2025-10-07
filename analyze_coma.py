E_coma = EllipticCurve(QQ, [-10141, 9980]) # Predicted curve for Coma

rank_coma = E_coma.rank() # Algebraic rank via 2-descent
print(f"Predicted Rank: {rank_coma}")

if rank_coma > 0:
    P_coma = E_coma.gens()[0] # Finds minimal generator point
    print(f"Generator: {P_coma}")
else:
    print("No generator (Rank 0)")
