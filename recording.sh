#!/bin/bash

RECORDINGS_DIR="./src/tracking/resources/secondWave"

# Étape 1 : récupérer tous les fichiers
mapfile -t files < <(find "$RECORDINGS_DIR" -type f)

# Étape 2 : reconstruire le chemin relatif et lancer le script
for file in "${files[@]}"; do
    # Enlever le préfixe jusqu'à secondWave/
    relative_path="${file#*secondWave/}"

    video_path="secondWave/$relative_path"

    echo "Processing: $video_path"
    python3 src/tracking/main.py --video_path "$video_path" --save_data
done