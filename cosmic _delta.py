# Define the elliptic curve over the rational numbers (QQ)
E = EllipticCurve(QQ, [-1706, 6320])

# Calculate the discriminant of the curve E
delta = E.discriminant()
print(delta)
