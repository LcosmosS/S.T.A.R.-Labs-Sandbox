# Define the elliptic curve over the rational numbers (QQ)
E = EllipticCurve(QQ, [-1706, 6320])

# Compute the real period with higher precision
omega_high_precision = E.period_lattice().real_period(prec=100)
print(omega_high_precision)
