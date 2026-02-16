# Simulation des trajectoires de corps autour d'un point fixe

## Description

Ce projet est une simulation d'une bille orbitant autour d'un poids sur un drap.
Celui-ci est modélisé en utilisant les lois newtoniennes.

## Prérequis

- Python >= 3.13

## Installation

Créer un environnement virtuel:

```bash/zsh
python3 -m venv venv
source venv/bin/activate
```

Installer les dépendances nécessaires, exécuter:

```bash/zsh
pip install -r requirements.txt
```

## Lancement de la simulation Newtonienne

Dans la racine du projet, exécuter:

```bash/zsh
cd src/simu_newtonienne && python3 main.py
```

## Lancement de la simulation avec machine learning

Dans la racine du projet, exécuter:

```bash/zsh
cd src/simu_machine_learning && python3 main.py
```

## Lancement du fichier de tracking de la balle

Dans la racine du projet, exécuter:

```bash/zsh
python src/tracking/main.py [--path_video PATH_VIDEO] [--save_images SAVE_IMAGES] [--save_data SAVE_DATA]
```
Où [] indique que les arguments sont optionnels, et:
- `--path_video PATH_VIDEO` : chemin vers la vidéo à traiter à partir du dossier `src/tracking/resources/`, par défaut `src/tracking/resources/big_blue.mp4`
- `--save_images SAVE_IMAGES` : indique si les images extraites de la vidéo doivent être sauvegardées, par défaut `False`
- `--save_data SAVE_DATA` : indique si les positions de la balle extraites de la vidéo doivent être sauvegardées dans un fichier CSV, par défaut `False`

### Nettoyage des images sauvegardées

Si vous avez choisi de sauvegarder les images extraites de la vidéo, elles seront stockées dans le dossier `src/tracking/outputs/outputs_images`.
Pareil pour les vidéos traitées, elles seront stockées dans le dossier `src/tracking/outputs/outputs_videos`.
Pour nettoyer ces dossiers et supprimer tout ce qui est sauvegardé, vous pouvez exécuter la commande suivante dans la racine du projet:

```bash/zsh
./src/tracking/cleanOutputs.sh
```

