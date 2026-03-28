# Review technique — 2026-03-28

30 problèmes identifiés. Classés par catégorie et priorité.

---

## Bugs

| # | Fichier | Ligne | Problème | Correction |
|---|---------|-------|---------|------------|
| 1 | `src/physics/mcu.py` | 9 | Import `deg_to_rad` inutilisé | Supprimer la ligne |
| 2 | `src/ml/models.py` | 115 | `predict_step` ne vérifie pas que `scaler_X` est initialisé avant `transform()` | Ajouter `hasattr(self, "scaler_X")` dans la garde |
| 3 | `src/ml/train.py` | ~206 | Si `r < 1e-6 px`, `vr`/`vtheta` explosent → entraînement instable | Clipper `r` à `r_min_px` avant la division |
| 4 | `src/ui/base_sim_widget.py` | `_stop()` | `thread.wait()` sans timeout → freeze si le thread se bloque | `thread.wait(5000)` puis `terminate()` |
| 5 | `src/ml/models.py` | 125 | Pas de détection NaN/Inf dans `delta` → trajectoire fictive silencieuse | `if np.isnan(delta).any(): raise RuntimeError(...)` |

---

## Incohérences

| # | Fichiers | Problème | Correction |
|---|---------|---------|------------|
| 6 | `predict.py` vs `cone.py` | Ordre des tests d'arrêt diverge : `cone.py` teste après update de position, `predict.py` avant → décalage ±1 pas | Aligner les deux sur la même logique |
| 7 | `ml.toml` vs `cone.toml` | `depth = 0.09` dupliqué sans validation croisée — si l'un change sans l'autre, les modèles ML apprennent sur un cône différent | Ajouter assertion dans `app.py` au démarrage |
| 8 | `src/app.py` | 89 | `n_passes` a un fallback `3` hardcodé ET une valeur dans la config — deux sources de vérité | Supprimer le fallback, lire uniquement depuis la config |
| 9 | `src/ui/main_window.py` | ~112 | `addItems()` émet `currentTextChanged` avant la connexion → `set_context` appelé deux fois | `blockSignals(True)` avant `addItems()`, `False` après |
| 10 | `src/scripts/generate_data.py` | 106 | Fusion `gen_cfg \| phys_cfg` implicite — si les deux ont une clé commune, `phys_cfg` écrase silencieusement | Merger explicitement clé par clé |

---

## Optimisations

| # | Fichier | Problème | Correction |
|---|---------|---------|------------|
| 11 | `src/ui/ml_widget.py` | `_load_synth_train_trajs()` relit le `.npz` depuis le disque à chaque `setup()` | Ajouter un cache instance `self._cached_synth_trajs` |
| 12 | `src/ml/train.py` | Les scalers de `LinearStepModel` et `MLPStepModel` divergent entre chunks quand entraînés en parallèle sur les mêmes données | Scaler partagé ou synchronisé |

---

## Qualité / documentation

| # | Fichier | Problème | Correction |
|---|---------|---------|------------|
| 13 | `src/ml/train.py` | ~185 | Seuil outlier `50.0` px magique non documenté (dépend résolution caméra) | Commenter : `# 50 px ≈ 3.7 cm @ 1350 px/m` |
| 14 | `src/scripts/test_ml_models.py` | 25 | `CONTEXT_COLORS` hardcodé — KeyError silencieux si on ajoute un contexte | Construire dynamiquement depuis `cfg["synth"]["contexts"]["names"]` |
| 15 | `src/ml/predict.py` | docstring | Unité de `v_stop` non précisée (m/s en synth, px/frame en réel) | Compléter la docstring |
| 16 | `src/ui/cone_widget.py` | ~89 | Formule `center_z` sans commentaire | Ajouter `# z_surface(r=0) + ball_radius` |
| 17 | `src/ml/train.py` | ~209 | Formule `vtheta = (xc*vy - yc*vx)/r` correcte mais non documentée | Ajouter commentaire dérivation polaire |
| 18 | `src/ui/ml_widget.py` | 52 | `parents[1]` fragile si la structure de répertoires change | `Path(__file__).resolve().parent.parent` avec commentaire |
| 19 | `src/ui/controls.py` | `__init__` | Docstring ne précise pas la structure de `cfg` attendue | Ajouter docstring avec structure `cfg["preset"]` / `cfg["ranges"]` |
| 20 | `src/config/loader.py` | `load_config` | Pas de gestion d'erreur — `FileNotFoundError` brute si fichier absent | Relever avec message clair : `f"Config introuvable : {name}.toml"` |

---

## Robustesse

| # | Fichier | Problème | Correction |
|---|---------|---------|------------|
| 21 | `src/physics/membrane.py` | ~45 | Pas d'assertion `center_radius > 0` ni `r_min <= R` | Ajouter assertions en tête de fonction |
| 22 | `src/ui/main_window.py` | `_make_tab()` | `sim_widget.setup()` au démarrage sans try-except → crash UI si config mal formée | Entourer d'un try-except avec log |

---

## Top 5 priorités

1. **#6** — Aligner conditions d'arrêt `compute_cone` ↔ `predict_trajectory`
2. **#7** — Valider `cone.toml.depth == ml.toml.synth.physics.depth` dans `app.py`
3. **#3** — Clipper `r_min_px` dans `_iter_real_pairs` (explosion vr/vtheta)
4. **#4** — Timeout sur `thread.wait()` dans `_stop()`
5. **#11** — Cache trajectoires de fond dans `ml_widget`
