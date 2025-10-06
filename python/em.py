from sage.all import EllipticCurve, QQ

# Standard curve from your research (Virgo Cluster, Document 4440)
a_standard = -1706
b_standard = 6320
E_standard = EllipticCurve(QQ, [0, 0, 0, a_standard, b_standard])
rank_standard = E_standard.rank()
print(f"Standard Curve Rank: {rank_standard}")

# EU-inspired EM term (rho_e * B proxy = 0.1, modulating b)
em_term = 0.1
b_em = b_standard + em_term * 6320  # Scale by b
E_em = EllipticCurve(QQ, [0, 0, 0, a_standard, b_em])
rank_em = E_em.rank()
print(f"EM-Modulated Curve Rank: {rank_em}")

# Simple "prediction" test: Does EM preserve or enhance rank?
improvement = rank_em == rank_standard
print(f"Rank Preserved: {improvement}")