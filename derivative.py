# Re-compute L'(E,1) with higher precision
L_derivative_high_precision = E.lseries().dokchitser(prec=100).derivative(1, 1)
print(L_derivative_high_precision)
