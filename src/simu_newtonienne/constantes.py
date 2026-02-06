G = 1.0          # constante gravitationnelle arbitraire
mu = 0.05        # coefficient de friction
dt = 0.01        # delta t
steps = 4000

# Soleil
sun_radius = 0.3
M_sun = 2.0      # masse du Soleil

# Drap
k_depth = 0.1
k_sigma = 2.0
depth = k_depth * M_sun
sigma = k_sigma * sun_radius

# Bille
x, y = 2.0, 0.0 # position initiale de la bille
vx, vy = 0.0, 1.0 # vitesse initiale de la bille
