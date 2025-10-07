# Define the elliptic curve over the rational numbers (QQ)
E = EllipticCurve(QQ, [-1706, 6320])

# Compute the regulator with higher precision
P = E.gens()[0]
regulator_high_precision = P.height(precision=100)
print(regulator_high_precision)
