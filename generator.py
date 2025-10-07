# Define the elliptic curve over the rational numbers (QQ)
E = EllipticCurve(QQ, [-1706, 6320])

# Find the generator(s) of the free part of the Mordell-Weil group
generators = E.gens()
print(generators)
