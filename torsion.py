# Define the elliptic curve over the rational numbers (QQ)
E = EllipticCurve(QQ, [-1706, 6320])

# Compute the torsion subgroup of E
torsion_subgroup = E.torsion_subgroup()
print(torsion_subgroup)
