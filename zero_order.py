# Compute the L-series associated with E
L = E.lseries()

# Compute the value of L(E,s) at s=1
L_value_at_1 = L(1)
print(L_value_at_1)

# Compute the value of the first derivative L'(E,s) at s=1
L_derivative_at_1 = L.dokchitser().derivative(1, 1)
print(L_derivative_at_1)
