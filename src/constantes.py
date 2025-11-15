# --- paramètres ---
G = 1.0          # constante gravitationnelle arbitraire
M_sun = 2.0      # masse du Soleil
mu = 0.05        # coefficient de friction
dt = 0.01        # delta t
steps = 4000

# Soleil et drap
sun_radius = 0.3
k_depth = 0.1
k_sigma = 2.0
depth = k_depth * M_sun
sigma = k_sigma * sun_radius