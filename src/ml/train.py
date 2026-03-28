"""Logique d'entraînement pour les deux modèles step.

Entraînement synthétique (train_synth) :
  1. Scalers partagés : fit_shared_scalers() échantillonne n_scaler_chunks
     répartis uniformément sur tous les chunks → stats représentatives de la
     distribution globale, identiques pour tous les workers.
  2. Split validation : derniers val_fraction% de chaque contexte réservés
     pour l'early stopping du MLP.
  3. LinearStepModel : 1 seule passe (équations normales exactes, l'ordre
     des chunks ne change pas le résultat).
  4. MLPStepModel : n_epochs passes avec shuffle des chunks à chaque epoch
     + early stopping sur le jeu de validation.

Entraînement réel (train_real) :
  Pré-passe pour calibrer les scalers sur toutes les expériences, puis
  n_passes avec shuffle de l'ordre des expériences pour le MLP.
"""

import gc
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ml.models import LinearStepModel, MLPStepModel, state_to_features

log = logging.getLogger(__name__)


# ── Utilitaires ───────────────────────────────────────────────────────────────


def _chunk_to_pairs(chunk_path: Path):
    """Charge un chunk .npz et retourne (X_features, y_features)."""
    data = np.load(chunk_path)
    X = state_to_features(data["X"].astype(np.float32))
    y = state_to_features(data["y"].astype(np.float32))
    return X, y


def fit_shared_scalers(
    chunk_paths: list[Path],
    n_sample: int = 10,
) -> tuple[StandardScaler, StandardScaler]:
    """Calibre scaler_X et scaler_y sur un échantillon uniforme de chunks.

    Les chunks sont tirés à intervalles réguliers sur toute la liste (pas
    seulement les premiers) pour que les statistiques soient représentatives
    de la distribution globale des états et des résidus.

    Retourne (scaler_X, scaler_y) fittés — à injecter dans les modèles avec
    inject_scalers() avant tout partial_fit().
    """
    n = len(chunk_paths)
    indices = np.linspace(0, n - 1, min(n_sample, n)).round().astype(int)
    indices = sorted(set(indices.tolist()))
    log.info("fit_shared_scalers : %d chunks échantillonnés sur %d", len(indices), n)

    X_parts, res_parts = [], []
    for i in indices:
        X, y = _chunk_to_pairs(chunk_paths[i])
        X_parts.append(X)
        res_parts.append(y - X)
        del y

    X_all   = np.vstack(X_parts)
    res_all = np.vstack(res_parts)
    scaler_X = StandardScaler().fit(X_all)
    scaler_y = StandardScaler().fit(res_all)
    log.info(
        "fit_shared_scalers : %d échantillons — X μ±σ ≈ [%.3f ± %.3f]",
        len(X_all), float(X_all.mean()), float(X_all.std()),
    )
    return scaler_X, scaler_y


def _compute_val_loss(
    model: "LinearStepModel | MLPStepModel",
    val_paths: list[Path],
) -> float:
    """MSE moyen en espace normalisé sur les chunks de validation."""
    losses = []
    for path in val_paths:
        X, y = _chunk_to_pairs(path)
        losses.append(model.val_loss(X, y))
        del X, y
    return float(np.mean(losses)) if losses else float("inf")


def _train_lr_context(
    chunk_paths: list[Path],
    val_paths: list[Path],
    models_dir: Path,
    context_name: str,
    scaler_X: StandardScaler,
    scaler_y: StandardScaler,
) -> str:
    """Entraîne LinearStepModel sur les chunks donnés. Retourne le nom du fichier sauvegardé.

    1 seule passe : les équations normales sont exactes, répéter les mêmes
    données biaise la régularisation sans améliorer la solution.
    Défini au niveau module pour être picklable par ProcessPoolExecutor.
    """
    logging.basicConfig(level=logging.INFO)
    _log = logging.getLogger(__name__)
    _log.info("LR [%s] : %d chunks train, %d val", context_name, len(chunk_paths), len(val_paths))

    lr_model = LinearStepModel()
    lr_model.inject_scalers(scaler_X, scaler_y)

    for i, path in enumerate(chunk_paths):
        X, y = _chunk_to_pairs(path)
        lr_model.partial_fit(X, y)
        del X, y
        gc.collect()
        if (i + 1) % 10 == 0:
            _log.info("  LR [%s] — chunk %d/%d", context_name, i + 1, len(chunk_paths))

    if val_paths:
        val = _compute_val_loss(lr_model, val_paths)
        _log.info("  LR [%s] — val MSE = %.6f (solution exacte)", context_name, val)

    name = f"synth_linear_{context_name}.pkl"
    lr_model.save(models_dir / name)
    _log.info("  LinearStepModel [%s] sauvegardé", context_name)
    return name


def _train_mlp_context(
    chunk_paths: list[Path],
    val_paths: list[Path],
    models_dir: Path,
    context_name: str,
    scaler_X: StandardScaler,
    scaler_y: StandardScaler,
    n_epochs: int = 5,
    patience: int = 2,
) -> str:
    """Entraîne MLPStepModel avec shuffle + early stopping. Retourne le nom du fichier sauvegardé.

    Boucle d'entraînement :
      - Chaque epoch : shuffle de l'ordre des chunks → 1 appel partial_fit() par chunk
        (= 1 epoch sklearn sur ce batch, grâce à max_iter=1 dans MLPRegressor).
      - Early stopping sur val_paths si disponible : sauvegarde le meilleur checkpoint.
    Défini au niveau module pour être picklable par ProcessPoolExecutor.
    """
    logging.basicConfig(level=logging.INFO)
    _log = logging.getLogger(__name__)
    _log.info(
        "MLP [%s] : %d chunks train, %d val, %d epochs max, patience=%d",
        context_name, len(chunk_paths), len(val_paths), n_epochs, patience,
    )

    model = MLPStepModel()
    model.inject_scalers(scaler_X, scaler_y)

    rng = np.random.default_rng(0)
    path = models_dir / f"synth_mlp_{context_name}.pkl"
    best_val = float("inf")
    n_bad = 0
    saved = False

    for epoch in range(n_epochs):
        order = rng.permutation(len(chunk_paths))
        for chunk_idx in order:
            X, y = _chunk_to_pairs(chunk_paths[int(chunk_idx)])
            model.partial_fit(X, y)
            del X, y
        gc.collect()
        _log.info("  MLP [%s] — epoch %d/%d terminée", context_name, epoch + 1, n_epochs)

        if not val_paths:
            continue  # pas d'early stopping sans validation, on complète toutes les epochs

        val = _compute_val_loss(model, val_paths)
        _log.info("  MLP [%s] — val MSE = %.6f", context_name, val)
        if val < best_val - 1e-7:
            best_val = val
            model.save(path)
            saved = True
            n_bad = 0
        else:
            n_bad += 1
            if n_bad >= patience:
                _log.info("  MLP [%s] — early stopping à l'epoch %d", context_name, epoch + 1)
                break

    if not saved:
        model.save(path)

    _log.info(
        "  MLPStepModel [%s] sauvegardé (best val MSE = %.6f)",
        context_name, best_val,
    )
    return path.name


# ── API publique ───────────────────────────────────────────────────────────────


def train_synth(
    data_dir: Path,
    models_dir: Path,
    contexts: dict,
    n_workers: int = 1,
    n_scaler_chunks: int = 10,
    val_fraction: float = 0.05,
    n_epochs: int = 5,
    patience: int = 2,
) -> None:
    """Entraîne 2 × len(contexts) modèles sur les données synthétiques.

    contexts       = {"10pct": 0.10, "50pct": 0.50, "100pct": 1.00}
    n_scaler_chunks : nombre de chunks échantillonnés uniformément pour calibrer
                      les scalers partagés (indépendants du contexte).
    val_fraction   : fraction des chunks de chaque contexte réservée à la
                     validation MLP (early stopping). 0 → pas d'early stopping.
    n_epochs       : nombre de passes MLP sur les données (shuffle à chaque passe).
    n_workers      : 1 → séquentiel ; > 1 → ProcessPoolExecutor.
    """
    all_chunks = sorted(data_dir.glob("chunk_*.npz"))
    if not all_chunks:
        raise FileNotFoundError(f"Aucun chunk trouvé dans {data_dir}")

    models_dir.mkdir(parents=True, exist_ok=True)
    n_total = len(all_chunks)

    # ── Scalers partagés (même pour tous les workers et tous les contextes) ──
    scaler_X, scaler_y = fit_shared_scalers(all_chunks, n_sample=n_scaler_chunks)

    # ── Construction des tâches ────────────────────────────────────────────────
    tasks:  list[tuple] = []
    labels: list[str]   = []

    for name, fraction in contexts.items():
        n_chunks = max(1, int(n_total * fraction))
        n_val    = max(0, min(int(n_chunks * val_fraction), n_chunks - 1))
        train_paths = all_chunks[:n_chunks - n_val]
        val_paths   = all_chunks[n_chunks - n_val:n_chunks]

        log.info(
            "Contexte [%s] : %d chunks train + %d val",
            name, len(train_paths), len(val_paths),
        )
        tasks.append((_train_lr_context,
                      train_paths, val_paths, models_dir, name, scaler_X, scaler_y))
        labels.append(f"linear_{name}")

        tasks.append((_train_mlp_context,
                      train_paths, val_paths, models_dir, name, scaler_X, scaler_y,
                      n_epochs, patience))
        labels.append(f"mlp_{name}")

    log.info("%d modèles à entraîner, %d worker(s)", len(tasks), n_workers)

    if n_workers == 1:
        for (fn, *args), label in zip(tasks, labels):
            log.info("▶ %s", label)
            fn(*args)
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = {
                executor.submit(fn, *args): label
                for (fn, *args), label in zip(tasks, labels)
            }
            for future in as_completed(futures):
                label = futures[future]
                try:
                    saved = future.result()
                    log.info("✓ %s", saved)
                except Exception as exc:
                    log.error("✗ Erreur [%s] : %s", label, exc)
                    raise


def compute_exp_centers(df: pd.DataFrame, tracking_cfg: dict) -> dict:
    """Estime le centre du cône pour chaque expérience depuis sa position finale.

    Algorithme :
      1. Pour chaque expérience, médiane des 15 dernières positions → endpoint_i.
      2. Centre de référence global = médiane de tous les endpoints.
      3. Outliers (endpoint à > 2 × MAD du centre de référence) → remplacés par
         le centre de référence.
      4. Chaque expérience est centrée sur son propre endpoint (ou le centre de
         référence pour les outliers).

    Cela corrige les offsets caméra inter-expériences sans dépendre de
    center_x/center_y dans la config (qui peut être approximatif).

    Retourne {expID: (cx_px, cy_px)}.
    """
    last_n = 15  # frames finales pour estimer la position d'arrêt

    raw: dict = {}
    for exp_id, group in df.groupby("expID"):
        tail   = group.sort_values("temps").tail(last_n)
        raw[exp_id] = (float(tail["x"].median()), float(tail["y"].median()))

    all_x = np.array([v[0] for v in raw.values()])
    all_y = np.array([v[1] for v in raw.values()])
    cx_ref = float(np.median(all_x))
    cy_ref = float(np.median(all_y))

    # Seuil outlier : 2 × MAD (Median Absolute Deviation) sur la distance au centre
    dists  = np.sqrt((all_x - cx_ref) ** 2 + (all_y - cy_ref) ** 2)
    mad    = float(np.median(np.abs(dists - np.median(dists))))
    thresh = max(2 * mad, 50.0)   # au moins 50 px ≈ 3.7 cm @ 1350 px/m

    n_valid = int((dists <= thresh).sum())
    log.info(
        "compute_exp_centers : centre de référence (%.1f, %.1f) px, "
        "%d/%d expériences dans le seuil (±%.0f px)",
        cx_ref, cy_ref, n_valid, len(raw), thresh,
    )

    return {
        eid: (cx, cy) if np.sqrt((cx - cx_ref) ** 2 + (cy - cy_ref) ** 2) <= thresh
             else (cx_ref, cy_ref)
        for eid, (cx, cy) in raw.items()
    }


def _iter_real_pairs(
    df: pd.DataFrame,
    centers: dict,
    r_min_px: float = 1.0,
    exp_order: list | None = None,
):
    """Génère (X_feat, y_feat) expérience par expérience depuis un DataFrame déjà chargé.

    Coordonnées en pixels centrées sur le centre propre à chaque expérience
    (correction de l'offset caméra via compute_exp_centers).
    Les vitesses (speedX, speedY) sont invariantes à la translation.
    r_min_px  : rayon minimum en pixels (= center_radius × px_per_meter) ; clippe le
                dénominateur pour éviter que vr/vtheta explosent quand la bille passe au centre.
    exp_order : ordre d'itération des expériences (liste d'expIDs).
                None → ordre trié par défaut. Passer une liste shufflée pour le MLP.
    """
    groups = {
        exp_id: grp.sort_values("temps")
        for exp_id, grp in df.groupby("expID")
    }
    if exp_order is None:
        exp_order = sorted(groups)
    for exp_id in exp_order:
        group = groups[exp_id]
        cx, cy = centers[exp_id]
        xc = group["x"].values     - cx
        yc = group["y"].values     - cy
        vx = group["speedX"].values
        vy = group["speedY"].values

        r      = np.sqrt(xc**2 + yc**2)
        theta  = np.arctan2(yc, xc)
        # Projection polaire : vr = (r⃗·v⃗)/r, vθ = (r⃗×v⃗)/r (composante z du produit vectoriel 2D)
        vr     = (xc * vx + yc * vy) / np.maximum(r, r_min_px)
        vtheta = (xc * vy - yc * vx) / np.maximum(r, r_min_px)

        states = np.column_stack([r, theta, vr, vtheta]).astype(np.float32)
        if len(states) < 2:
            continue
        yield state_to_features(states[:-1]), state_to_features(states[1:])


def train_real(csv_path: Path, tracking_cfg: dict, n_passes: int = 3) -> tuple:
    """Charge le CSV de tracking, entraîne LR + MLP, retourne (lr_model, mlp_model).

    Pipeline :
      1. Pré-passe sur TOUTES les expériences → scalers calibrés sur la distribution
         globale (pas seulement la première expérience vue).
      2. LR : 1 passe (solution exacte, ordre sans importance).
      3. MLP : n_passes passes avec ordre des expériences shufflé à chaque passe.

    Les modèles sont retournés en mémoire (non sauvegardés sur disque).
    """
    df = pd.read_csv(csv_path, sep=";", skipinitialspace=True)
    df.columns = df.columns.str.strip()
    centers  = compute_exp_centers(df, tracking_cfg)
    r_min_px = tracking_cfg.get("center_radius", 0.03) * tracking_cfg.get("px_per_meter", 1350.0)
    exp_ids  = sorted(df["expID"].unique().tolist())

    # ── Pré-passe : calibrage des scalers sur toutes les expériences ──────────
    log.info("train_real — pré-passe scaler sur %d expériences", len(exp_ids))
    X_parts, res_parts = [], []
    for X_feat, y_feat in _iter_real_pairs(df, centers, r_min_px):
        X_parts.append(X_feat)
        res_parts.append(y_feat - X_feat)
    if not X_parts:
        raise ValueError("Aucune paire d'entraînement extraite du CSV de tracking")
    scaler_X = StandardScaler().fit(np.vstack(X_parts))
    scaler_y = StandardScaler().fit(np.vstack(res_parts))
    del X_parts, res_parts
    gc.collect()

    lr_model  = LinearStepModel()
    mlp_model = MLPStepModel()
    lr_model.inject_scalers(scaler_X, scaler_y)
    mlp_model.inject_scalers(scaler_X, scaler_y)

    # ── LR : 1 passe (équations normales — ordre et répétitions sans effet) ───
    log.info("train_real — LR : 1 passe")
    for X_feat, y_feat in _iter_real_pairs(df, centers, r_min_px):
        lr_model.partial_fit(X_feat, y_feat)
    gc.collect()

    # ── MLP : n_passes avec shuffle pour éviter le biais de séquence ─────────
    rng = np.random.default_rng(0)
    for pass_idx in range(n_passes):
        order = rng.permutation(exp_ids).tolist()
        log.info("train_real — MLP pass %d/%d (ordre shufflé)", pass_idx + 1, n_passes)
        for X_feat, y_feat in _iter_real_pairs(df, centers, r_min_px, exp_order=order):
            mlp_model.partial_fit(X_feat, y_feat)
        gc.collect()

    return lr_model, mlp_model
