import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from tracking_data_parser import parse_tracking_csv


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


csv_path = Path(__file__).resolve().parents[3] / "data" / "tracking_data.csv"
data, mass_center = parse_tracking_csv(csv_path, center_mode="auto")

if not data:
    raise ValueError("Aucune trajectoire valide trouvée dans tracking_data.csv")

X = []
Y = []

min_trajectory_len = min(len(sample["trajectory"]) for sample in data)

for sample in data:
    # Entrée : conditions initiales
    X.append(sample["initial"])
    # Sortie : trajectoire formatée en un vecteur
    traj = sample["trajectory"][:min_trajectory_len]
    flat_traj = []
    for point in traj:
        for coord in point:
            flat_traj.append(coord)
    Y.append(flat_traj)

X = np.array(X, dtype=np.float32)
Y = np.array(Y, dtype=np.float32)

print("Nombre d'échantillons:", len(data))
print("Masse centrale estimée (px):", mass_center)
print("Longueur minimale commune utilisée pour l'entraînement:", min_trajectory_len)
print("Shape X:", X.shape)  # (n_samples, 4)
print("Shape Y:", Y.shape)  # (n_samples, 2 * min_trajectory_len)

model = LinearRegression()
model.fit(X, Y)

Y_pred = model.predict(X)

mse = mean_squared_error(Y, Y_pred)
print("MSE:", mse)

x_test = np.array([data[0]["initial"]], dtype=np.float32)

pred = model.predict(x_test)

pred_traj = pred.reshape(
    -1, 2
)  # reshape pour obtenir une trajectoire de points (x, y) à partir du vecteur prédit.
print("Trajectoire prédite:")
print(pred_traj)

true_traj = np.array(data[0]["trajectory"][:min_trajectory_len])
plot_trajectories(true_traj, pred_traj)
