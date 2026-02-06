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
python3 src/tracking/main.py [PATH_VIDEO] [SAVE IMAGES]
```
Où:
- `[PATH_VIDEO]` est le chemin à partir du dossier `src/tracking/resources` vers la vidéo à traiter. Par défaut, il est réglé sur `/first/big_blue.mp4`.
- `[SAVE IMAGES]` est un booléen (True/False) indiquant s'il faut sauvegarder les images extraites de la vidéo. Par défaut, il est réglé sur False.

### Nettoyage des images sauvegardées
