# Define the elliptic curve over the rational numbers (QQ)
E = EllipticCurve(QQ, [-1706, 6320])

# Compute the product of the Tamagawa numbers
tamagawa_product = prod(E.tamagawa_numbers())
print(tamagawa_product)
