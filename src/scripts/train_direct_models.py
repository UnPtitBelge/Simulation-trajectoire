"""CLI — Entraîne les modèles directs CI → trajectoire sur données synthétiques.

Délègue toute la logique à ml/train_direct.py (train_direct_synth).

Modèles produits dans data/models/ :
  direct_linear_{1pct,10pct,50pct,100pct}.pkl
  direct_mlp_{1pct,10pct,50pct,100pct}.pkl

Usage :
    python src/scripts/train_direct_models.py
    python src/scripts/train_direct_models.py --n-trajectories 20000
    python src/scripts/train_direct_models.py --max-steps 500
    python src/scripts/train_direct_models.py --no-save   # dry-run
"""

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

from config.loader import load_config
from ml.train_direct import train_direct_synth


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Entraîne les modèles directs CI→trajectoire sur données synthétiques."
    )
    parser.add_argument(
        "--n-trajectories", type=int, default=50_000,
        help="Trajectoires totales générées (contexte 100pct). Défaut : 50 000.",
    )
    parser.add_argument(
        "--max-steps", type=int, default=1_000,
        help="Longueur max de la trajectoire cible (pas). Défaut : 1 000 (= 10 s à dt=0.01).",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Dossier de sauvegarde des .pkl. Défaut : data/models/ de la config.",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Dry-run : entraîne mais ne sauvegarde pas les modèles.",
    )
    args = parser.parse_args()

    cfg        = load_config("ml")
    phys_cfg   = {**cfg["physics"], **cfg["synth"]["physics"]}
    gen_cfg    = cfg["synth"]["generation"]
    ctx_names  = cfg["synth"]["contexts"]["names"]
    ctx_fracs  = cfg["synth"]["contexts"]["fractions"]
    contexts   = dict(zip(ctx_names, ctx_fracs))
    models_dir = (
        args.output_dir
        if args.output_dir is not None
        else ROOT / cfg["paths"]["models_dir"]
    )

    print(f"\n{'═' * 60}")
    print(f"  Modèles directs CI → trajectoire")
    print(f"  n_trajectories={args.n_trajectories:,}  max_steps={args.max_steps}")
    print(f"  Contextes : {list(contexts.keys())}")
    print(f"  Sauvegarde : {'(désactivée, --no-save)' if args.no_save else models_dir}")
    print(f"{'═' * 60}\n")

    if args.no_save:
        # dry-run : pointe vers /tmp pour que save() ne pollue pas data/models/
        import tempfile
        tmp_dir = Path(tempfile.mkdtemp())
        effective_dir = tmp_dir
    else:
        effective_dir = models_dir

    results = train_direct_synth(
        phys_cfg   = phys_cfg,
        gen_cfg    = gen_cfg,
        contexts   = contexts,
        n_total    = args.n_trajectories,
        max_steps  = args.max_steps,
        models_dir = effective_dir,
        seed       = 0,
    )

    print(f"\n{'═' * 60}")
    print(f"  {'Fichier':<35} {'n_train':>8}  {'MAE r_train':>12}")
    print(f"  {'─' * 58}")
    for fname, model in results.items():
        print(f"  {fname:<35} {model.n_train:>8,}  {model.mae_r_train:>11.5f} m")
    print(f"{'═' * 60}\n")

    if args.no_save:
        print("Mode --no-save : fichiers temporaires supprimés.")
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
