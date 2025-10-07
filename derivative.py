# Define the elliptic curve over the rational numbers (QQ)
E = EllipticCurve(QQ, [-1706, 6320])

# Re-compute L'(E,1) with higher precision
L_derivative_high_precision = E.lseries().dokchitser(prec=100).derivative(1, 1)
print(L_derivative_high_precision)
