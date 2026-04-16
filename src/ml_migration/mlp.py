import numpy as np
from sklearn.neural_network import MLPRegressor
import matplotlib.pyplot as plt
import csv
from pathlib import Path


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


def estimate_mass_center(grouped_rows):
    all_x = []
    all_y = []

    for rows in grouped_rows.values():
        for point in rows:
            all_x.append(point["x"])
            all_y.append(point["y"])

    if not all_x or not all_y:
        return 0.0, 0.0

    return float(np.median(all_x)), float(np.median(all_y))


def parse_tracking_csv(csv_path, center_mode="auto"):
    grouped_rows = {}

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
            exp_id = clean_row["expID"]

            if exp_id not in grouped_rows:
                grouped_rows[exp_id] = []

            grouped_rows[exp_id].append(
                {
                    "temps": float(clean_row["temps"]),
                    "x": float(clean_row["x"]),
                    "y": float(clean_row["y"]),
                    "speedX": float(clean_row["speedX"]),
                    "speedY": float(clean_row["speedY"]),
                }
            )

    if center_mode == "auto":
        center_x, center_y = estimate_mass_center(grouped_rows)
    elif center_mode is None:
        center_x, center_y = 0.0, 0.0
    else:
        center_x, center_y = center_mode

    parsed_data = []
    for exp_id in sorted(grouped_rows.keys(), key=lambda value: int(value)):
        rows = grouped_rows[exp_id]
        rows.sort(key=lambda point: point["temps"])

        first_point = rows[0]
        sample = {
            "initial": (
                first_point["x"] - center_x,
                first_point["y"] - center_y,
                first_point["speedX"],
                first_point["speedY"],
            ),
            "trajectory": [
                (point["x"] - center_x, point["y"] - center_y)
                for point in rows
            ],
        }
        parsed_data.append(sample)

    return parsed_data, (center_x, center_y)


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

model = MLPRegressor(hidden_layer_sizes=(100,), max_iter=500, random_state=42) 
model.fit(X, Y)

Y_pred = model.predict(X)

x_test = np.array([data[0]["initial"]], dtype=np.float32)

pred = model.predict(x_test)

pred_traj = pred.reshape(
    -1, 2
)  # reshape pour obtenir une trajectoire de points (x, y) à partir du vecteur prédit.
print("Trajectoire prédite:")
print(pred_traj)

true_traj = np.array(data[0]["trajectory"][:min_trajectory_len])
plot_trajectories(true_traj, pred_traj)
