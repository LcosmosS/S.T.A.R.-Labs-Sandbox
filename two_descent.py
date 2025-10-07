# Define the elliptic curve over the rational numbers (QQ)
E = EllipticCurve(QQ, [-1706, 6320])

# Perform a verbose 2-descent to analyze the 2-Selmer group
E.two_descent(verbose=True)
