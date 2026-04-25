"""
Graphique de cross-validation épuré pour rapport scientifique.
Affiche les RMSE par fold (linéaire vs MLP) avec cartes de résumé.

Intégration dans migration_study.py :
    from plot_cv_results import plot_cv_results
    plot_cv_results(rmse_linear_all, rmse_mlp_all, k=k,
                    output_path=args.output_dir / "cv_results.png",
                    show=not args.no_show)
"""

from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.lines as mlines
import numpy as np


def plot_cv_results(
    rmse_linear: list[float],
    rmse_mlp: list[float],
    k: int = 5,
    output_path: Path | None = None,
    show: bool = True,
) -> plt.Figure:

    lin = np.array(rmse_linear)
    mlp = np.array(rmse_mlp)
    folds = [f"Fold {i+1}" for i in range(len(lin))]

    COLOR_LIN  = "#BA7517"
    COLOR_MLP  = "#185FA5"
    CARD_BG    = "#f5f5f3"
    ALPHA_MEAN = 0.35

    # Mise en page : cartes (ligne 0) + graphe (ligne 1)
    fig = plt.figure(figsize=(8, 5.8), facecolor="white")
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 3.0], hspace=0.38, wspace=0.25)

    ax_lin  = fig.add_subplot(gs[0, 0])
    ax_mlp  = fig.add_subplot(gs[0, 1])
    ax_main = fig.add_subplot(gs[1, :])

    # ── Cartes de résumé ──────────────────────────────────────────────────────
    def _summary_card(ax, title, values):
        ax.set_facecolor(CARD_BG)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])

        ax.text(0.5, 0.82, title,
                transform=ax.transAxes, ha="center", va="top",
                fontsize=9, color="#555555")
        ax.text(0.5, 0.50, f"{values.mean():.5f} m",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=15, fontweight="bold", color="#1a1a1a")
        ax.text(0.5, 0.10, f"σ = {values.std():.5f}",
                transform=ax.transAxes, ha="center", va="bottom",
                fontsize=8, color="#888888")

    _summary_card(ax_lin, "Linéaire — RMSE rayon moyen", lin)
    _summary_card(ax_mlp, "MLP — RMSE rayon moyen",      mlp)

    # ── Graphe principal ──────────────────────────────────────────────────────
    ax = ax_main
    ax.set_facecolor("#fafafa")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color("#dddddd")
    ax.spines["left"].set_linewidth(0.8)
    ax.tick_params(length=0, labelsize=10.5)
    ax.yaxis.grid(True, color="#e8e8e8", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)

    xs = np.arange(len(folds))

    # Lignes de tendance
    ax.plot(xs, lin, color=COLOR_LIN, linewidth=1.5, linestyle=(0, (5, 3)),
            zorder=2, alpha=0.85)
    ax.plot(xs, mlp, color=COLOR_MLP, linewidth=1.5, zorder=2, alpha=0.85)

    # Points par fold
    ax.scatter(xs, lin, s=55, facecolors="white", edgecolors=COLOR_LIN,
               linewidths=1.8, zorder=4)
    ax.scatter(xs, mlp, s=55, facecolors="white", edgecolors=COLOR_MLP,
               linewidths=1.8, zorder=4)

    # Lignes de moyenne (pointillés discrets)
    ax.axhline(lin.mean(), color=COLOR_LIN, linewidth=1.0,
               linestyle=(0, (2, 2)), alpha=ALPHA_MEAN, zorder=1)
    ax.axhline(mlp.mean(), color=COLOR_MLP, linewidth=1.0,
               linestyle=(0, (2, 2)), alpha=ALPHA_MEAN, zorder=1)

    # Valeurs sur chaque point
    y_margin = (max(lin.max(), mlp.max()) - min(lin.min(), mlp.min())) * 0.08
    for i, (vl, vm) in enumerate(zip(lin, mlp)):
        ax.text(i, vl + y_margin, f"{vl:.5f}", ha="center", va="bottom",
                fontsize=7.5, color=COLOR_LIN)
        ax.text(i, vm - y_margin, f"{vm:.5f}", ha="center", va="top",
                fontsize=7.5, color=COLOR_MLP)

    ax.set_xticks(xs)
    ax.set_xticklabels(folds, fontsize=10.5)
    ax.set_ylabel("RMSE rayon (m)", fontsize=10, color="#555555")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.4f}"))

    pad = (max(lin.max(), mlp.max()) - min(lin.min(), mlp.min())) * 0.5
    ax.set_ylim(min(lin.min(), mlp.min()) - pad,
                max(lin.max(), mlp.max()) + pad)
    ax.set_xlim(-0.4, len(folds) - 0.6)

    # Légende sous le graphe
    legend_elems = [
        mlines.Line2D([0], [0], color=COLOR_LIN, linewidth=1.5,
                      linestyle=(0, (5, 3)), marker="o", markersize=5,
                      markerfacecolor="white", markeredgecolor=COLOR_LIN,
                      label="Linéaire"),
        mlines.Line2D([0], [0], color=COLOR_MLP, linewidth=1.5,
                      marker="o", markersize=5,
                      markerfacecolor="white", markeredgecolor=COLOR_MLP,
                      label="MLP"),
        mlines.Line2D([0], [0], color="#aaaaaa", linewidth=1.0,
                      linestyle=(0, (2, 2)), label="Moyenne par modèle"),
    ]
    ax.legend(handles=legend_elems, fontsize=9, framealpha=0.9,
              edgecolor="#dddddd", loc="lower center",
              bbox_to_anchor=(0.5, -0.18), ncol=3)

    fig.suptitle(f"Validation croisée {k}-fold — 90 000 expériences",
                 fontsize=12, y=1.01, color="#222222", fontweight="normal")

    fig.tight_layout()

    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=180, bbox_inches="tight")
        print(f"Figure sauvegardée : {output_path}")

    if show:
        plt.show()

    return fig


if __name__ == "__main__":
    rmse_linear_all = [0.00841, 0.00842, 0.00841, 0.00841, 0.00840]
    rmse_mlp_all    = [0.00748, 0.00630, 0.00536, 0.00536, 0.00374]

    plot_cv_results(
        rmse_linear=rmse_linear_all,
        rmse_mlp=rmse_mlp_all,
        k=5,
        output_path=Path("figures/migration/cv_results.png"),
        show=True,
    )
