#!/usr/bin/env bash
# run_all.sh — Génère toutes les figures et résultats du projet.
#
# Ordre d'exécution :
#   1. Prérequis      : generate_data, train_models  (sautés si déjà présents)
#   2. Physique pure  : benchmark_integrators, benchmark_physics_levels
#   3. ML synthétique : benchmark_linear, benchmark_mlp, ablation_features,
#                       analyze_ml_error, collect_metrics
#   4. Comparaison    : compare_approaches  (nécessite tracking_data.csv)
#   5. Pédagogique    : demo_regression_lineaire, demo_mlp_direct  (nécessite tracking_data.csv)
#   6. Direct synth   : train_direct_models, benchmark_direct
#
# Usage :
#   ./run_all.sh              # tous les scripts, --no-plot (mode batch)
#   ./run_all.sh --plot       # affiche les fenêtres graphiques
#   ./run_all.sh --regen      # force la regénération des données et modèles
#   ./run_all.sh --skip-heavy # saute generate_data et train_models

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/src"
PYTHON="${PYTHON:-python3}"
WORKERS="${WORKERS:-$(nproc)}"

NO_PLOT="--no-plot"
REGEN=0
SKIP_HEAVY=0

for arg in "$@"; do
    case "$arg" in
        --plot)        NO_PLOT="" ;;
        --regen)       REGEN=1 ;;
        --skip-heavy)  SKIP_HEAVY=1 ;;
    esac
done

# ── Helpers ──────────────────────────────────────────────────────────────────

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $*"; }
skip() { echo -e "${YELLOW}⟳${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; }

run() {
    local label="$1"; shift
    echo ""
    echo -e "${GREEN}▶ $label${NC}"
    if $PYTHON "$@"; then
        ok "$label"
    else
        fail "$label — code de retour $?"
        exit 1
    fi
}

# ── 1. Prérequis ─────────────────────────────────────────────────────────────

SYNTH_DIR="$SRC/data/synthetic"
MODELS_DIR="$SRC/data/models"
N_CHUNKS=$(ls "$SYNTH_DIR"/chunk_*.npz 2>/dev/null | wc -l)
N_MODELS=$(ls "$MODELS_DIR"/synth_*.pkl 2>/dev/null | wc -l)
N_DIRECT=$(ls "$MODELS_DIR"/direct_*.pkl 2>/dev/null | wc -l)

if [[ $SKIP_HEAVY -eq 1 ]]; then
    skip "generate_data.py — ignoré (--skip-heavy)"
    skip "train_models.py  — ignoré (--skip-heavy)"
else
    if [[ $REGEN -eq 1 || $N_CHUNKS -eq 0 ]]; then
        run "Génération des données synthétiques" \
            "$SRC/scripts/generate_data.py" --workers "$WORKERS"
    else
        skip "generate_data.py — $N_CHUNKS chunks déjà présents"
    fi

    if [[ $REGEN -eq 1 || $N_MODELS -lt 8 ]]; then
        run "Entraînement des 8 modèles synthétiques" \
            "$SRC/scripts/train_models.py" --workers 8
    else
        skip "train_models.py — $N_MODELS modèles déjà présents"
    fi
fi

# ── 2. Physique pure ──────────────────────────────────────────────────────────

run "Convergence des intégrateurs" \
    "$SRC/scripts/benchmark_integrators.py" $NO_PLOT

run "Niveaux de précision physique (L0–L3)" \
    "$SRC/scripts/benchmark_physics_levels.py" $NO_PLOT

# ── 3. ML synthétique ─────────────────────────────────────────────────────────

run "Convergence LinearStepModel" \
    "$SRC/scripts/benchmark_linear.py" $NO_PLOT --workers "$WORKERS"

run "Convergence MLPStepModel" \
    "$SRC/scripts/benchmark_mlp.py" $NO_PLOT --workers "$WORKERS"

run "Ablation des features" \
    "$SRC/scripts/ablation_features.py" $NO_PLOT

run "Accumulation d'erreur ML" \
    "$SRC/scripts/analyze_ml_error.py" $NO_PLOT

run "Métriques consolidées des 8 modèles" \
    "$SRC/scripts/collect_metrics.py"

# ── 4. Comparaison tracking réel ─────────────────────────────────────────────

TRACKING="$SRC/data/tracking_data.csv"
if [[ -f "$TRACKING" ]]; then
    run "Comparaison physique / ML / tracking réel" \
        "$SRC/scripts/compare_approaches.py" $NO_PLOT
else
    skip "compare_approaches.py — $TRACKING absent"
fi

# ── 5. Modèles pédagogiques (approche directe CI → trajectoire) ──────────────

if [[ -f "$TRACKING" ]]; then
    run "Régression linéaire directe (version corrigée)" \
        "$SRC/scripts/demo_regression_lineaire.py" $NO_PLOT

    run "MLP direct (version corrigée)" \
        "$SRC/scripts/demo_mlp_direct.py" $NO_PLOT
else
    skip "demo_regression_lineaire.py — $TRACKING absent"
    skip "demo_mlp_direct.py          — $TRACKING absent"
fi

# ── 6. Modèles directs sur données synthétiques ──────────────────────────────

if [[ $REGEN -eq 1 || $N_DIRECT -lt 8 ]]; then
    run "Entraînement des 8 modèles directs (CI→trajectoire, synthétique)" \
        "$SRC/scripts/train_direct_models.py"
else
    skip "train_direct_models.py — $N_DIRECT modèles direct déjà présents"
fi

run "Benchmark direct vs step-by-step" \
    "$SRC/scripts/benchmark_direct.py" $NO_PLOT

# ── Récapitulatif ─────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════"
echo "  Figures  : $(ls "$SCRIPT_DIR/figures/"*.png 2>/dev/null | wc -l) fichiers dans figures/"
echo "  Résultats : $(ls "$SCRIPT_DIR/results/"*.csv 2>/dev/null | wc -l) fichiers dans results/"
echo "════════════════════════════════════════════"
