gravity_constant = 1.0  # Arbitrary gravitational constant
friction_coefficient = 0.05  # Linear friction/damping coefficient
time_step = 0.01  # Integration time step (seconds or arbitrary units)
num_steps = 4000  # Number of integration steps

# Central body (e.g., massive object at the center)
central_body_radius = 0.3
central_body_mass = 2.0  # Mass of the central body

# Deformable surface (e.g., curved surface parameters)
deformation_depth_scale = 0.1
deformation_sigma_scale = 2.0
surface_depth = deformation_depth_scale * central_body_mass
surface_sigma = deformation_sigma_scale * central_body_radius

# Moving object (e.g., test particle)
initial_position_x, initial_position_y = 2.0, 0.0  # Initial position
initial_velocity_x, initial_velocity_y = 0.0, 1.0  # Initial velocity
