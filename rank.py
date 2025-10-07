# Define the elliptic curve over the rational numbers (QQ)
E = EllipticCurve(QQ, [-1706, 6320])

# Compute the algebraic rank of E
algebraic_rank = E.rank()
print(algebraic_rank)
