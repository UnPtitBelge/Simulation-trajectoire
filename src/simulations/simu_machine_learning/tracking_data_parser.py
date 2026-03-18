import csv

import numpy as np


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
