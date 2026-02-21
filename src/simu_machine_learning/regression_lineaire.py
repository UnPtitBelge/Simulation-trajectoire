import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt


def plot_trajectories(true_traj, pred_traj):
    plt.figure(figsize=(8, 8))
    plt.plot(
        true_traj[:, 0], true_traj[:, 1], label="Vraie", linewidth=2, linestyle="-"
    )
    plt.plot(
        pred_traj[:, 0], pred_traj[:, 1], label="Prédite", linewidth=2, linestyle="--"
    )
    plt.scatter([0], [0], label="Masse centrale", s=100, color="red")
    plt.legend()
    plt.axis("equal")
    plt.grid(True)
    plt.show()


data = [
    {
        "initial": (1.0, 0.0, 0.0, 1.2),
        "trajectory": [
            (0.99, 0.06),
            (0.97, 0.12),
            (0.94, 0.18),
            (0.90, 0.24),
            (0.85, 0.30),
            (0.79, 0.35),
            (0.72, 0.40),
            (0.64, 0.44),
            (0.55, 0.48),
            (0.45, 0.51),
            (0.35, 0.53),
            (0.24, 0.54),
            (0.13, 0.54),
            (0.02, 0.53),
            (-0.09, 0.51),
            (-0.20, 0.48),
            (-0.30, 0.44),
            (-0.39, 0.39),
            (-0.47, 0.33),
            (-0.54, 0.26),
        ],
    },
    {
        "initial": (1.5, 0.0, 0.0, 1.0),
        "trajectory": [
            (1.49, 0.05),
            (1.47, 0.10),
            (1.44, 0.15),
            (1.40, 0.20),
            (1.35, 0.25),
            (1.29, 0.29),
            (1.22, 0.33),
            (1.14, 0.36),
            (1.05, 0.39),
            (0.95, 0.41),
            (0.85, 0.42),
            (0.74, 0.43),
            (0.63, 0.43),
            (0.52, 0.42),
            (0.41, 0.40),
            (0.30, 0.37),
            (0.20, 0.33),
            (0.11, 0.28),
            (0.03, 0.22),
            (-0.04, 0.15),
        ],
    },
    {
        "initial": (0.8, 0.0, 0.0, 1.4),
        "trajectory": [
            (0.79, 0.07),
            (0.76, 0.14),
            (0.72, 0.21),
            (0.66, 0.27),
            (0.59, 0.33),
            (0.51, 0.38),
            (0.42, 0.42),
            (0.32, 0.45),
            (0.21, 0.47),
            (0.10, 0.48),
            (-0.01, 0.48),
            (-0.12, 0.47),
            (-0.23, 0.45),
            (-0.33, 0.42),
            (-0.42, 0.38),
            (-0.50, 0.33),
            (-0.57, 0.27),
            (-0.63, 0.20),
            (-0.68, 0.12),
            (-0.72, 0.04),
        ],
    },
]

X = []
Y = []

for sample in data:
    # Entrée : conditions initiales
    X.append(sample["initial"])
    # Sortie : trajectoire formatée en un vecteur
    traj = sample["trajectory"]
    flat_traj = []
    for point in traj:
        for coord in point:
            flat_traj.append(coord)
    Y.append(flat_traj)

X = np.array(X, dtype=np.float32)
Y = np.array(Y, dtype=np.float32)

print("Shape X:", X.shape)  # (n_samples, 4)
print("Shape Y:", Y.shape)  # (n_samples, 40)

model = LinearRegression()
model.fit(X, Y)

Y_pred = model.predict(X)

mse = mean_squared_error(Y, Y_pred)
print("MSE:", mse)

x_test = np.array([[1.0, 0.0, 0.0, 1.2]], dtype=np.float32)

pred = model.predict(x_test)

pred_traj = pred.reshape(
    20, 2
)  # reshape pour obtenir une trajectoire 20 points x 2 coordonnées
print("Trajectoire prédite:")
print(pred_traj)

true_traj = np.array(data[0]["trajectory"])
plot_trajectories(true_traj, pred_traj)
