# Define the input data for the Coma Cluster
r_coma = 321
rho_coma = 9980

# Use the SAME scaling factor kappa derived from Virgo
kappa = 31.59259259259259

# Calculate the predicted coefficients for the Coma Cluster's curve
a_predicted_coma = -kappa * r_coma
b_predicted_coma = rho_coma

print(f"Predicted a for Coma Cluster: {a_predicted_coma}")
print(f"Predicted b for Coma Cluster: {b_predicted_coma}")
