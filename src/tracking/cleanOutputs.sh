#! /bin/bash

set -euo pipefail

base="./src/tracking/outputs"
dirs=("output_images" "output_videos")

for d in "${dirs[@]}"; do
  p="$base/$d"
  if [[ -d "$p" ]]; then
    # supprime tout le contenu du dossier, y compris fichiers "cachés"
    rm -rf -- "$p"/* "$p"/.[!.]* "$p"/..?* 2>/dev/null || true
    echo "✅ Nettoyé: $p"
  else
    echo "⚠️  Dossier absent, ignoré: $p"
  fi
done
