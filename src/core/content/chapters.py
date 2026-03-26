"""Chapters — timeline data for the presentation mode.

Each chapter maps to one or several simulation steps.
No theory text overlays — the presentation is purely simulation-based.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChapterStep:
    """One simulation step within a chapter.

    kind: always "sim" (theory steps removed)
    sim_key: simulation to show
    preset: preset name to apply (None = current/default params)
    text: short overlay text shown during this step
    """

    kind: str  # "sim"
    text: str = ""
    sim_key: str | None = None
    preset: str | None = None


@dataclass(frozen=True)
class Chapter:
    """A chapter in the presentation timeline."""

    number: int
    title: str
    short: str  # one-line summary for the timeline bar
    theory_key: str  # kept for reference, unused in presentation
    steps: tuple[ChapterStep, ...] = field(default_factory=tuple)


# ── 6 chapters — one per simulation theme ────────────────────────────────────

CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        number=1,
        title="MCU — Modèle prescriptif",
        short="Cercle parfait, formule exacte, zéro erreur numérique",
        theory_key="mcu",
        steps=(
            ChapterStep(
                kind="sim", sim_key="mcu",
                text="x(t) = R·cos(ωt) — la position est calculée, pas simulée.",
            ),
        ),
    ),
    Chapter(
        number=2,
        title="Cône — Newton + frottement de Coulomb",
        short="Orbites en rosette, précession ~151°/tour",
        theory_key="newton_cone",
        steps=(
            ChapterStep(
                kind="sim", sim_key="cone", preset="presentation",
                text="La bille spirale vers le centre sous l'effet du frottement.",
            ),
            ChapterStep(
                kind="sim", sim_key="cone", preset="sans_frottement",
                text="Sans frottement : le moment cinétique se conserve.",
            ),
        ),
    ),
    Chapter(
        number=3,
        title="Membrane de Laplace vs Cône",
        short="Plus d'équations ≠ meilleur modèle",
        theory_key="laplace_membrane",
        steps=(
            ChapterStep(
                kind="sim", sim_key="membrane", preset="presentation",
                text="z(r) = −A·ln(R/r) — pente en 1/r, force variable.",
            ),
            ChapterStep(
                kind="sim", sim_key="cone", preset="presentation",
                text=(
                    "Notre surface réelle se comporte comme un cône (pente constante) — "
                    "le modèle de Newton est plus fidèle à l'expérience."
                ),
            ),
        ),
    ),
    Chapter(
        number=4,
        title="Intégration numérique",
        short="Euler vs Verlet vs RK4",
        theory_key="integration",
        steps=(
            ChapterStep(
                kind="sim", sim_key="cone", preset="euler",
                text="Euler semi-implicite (ordre 1) : v←v+a·Δt, x←x+v·Δt.",
            ),
            ChapterStep(
                kind="sim", sim_key="cone", preset="verlet",
                text="Verlet (ordre 2, symplectique) : conserve l'énergie à long terme.",
            ),
            ChapterStep(
                kind="sim", sim_key="cone", preset="rk4",
                text="RK4 (ordre 4) : 4 évaluations par pas, ultra-précis.",
            ),
            ChapterStep(
                kind="sim", sim_key="cone", preset="compare",
                text="Superposition : Euler (rouge) / Verlet (vert) / RK4 (bleu).",
            ),
        ),
    ),
    Chapter(
        number=5,
        title="Machine Learning — données réelles",
        short="Apprendre depuis les trajectoires filmées",
        theory_key="machine_learning",
        steps=(
            ChapterStep(
                kind="sim", sim_key="ml", preset="donnees_completes",
                text="Régression linéaire entraînée sur 15 trajectoires réelles.",
            ),
            ChapterStep(
                kind="sim", sim_key="ml",
                text="Toggle RL / MLP — même données, modèle plus expressif.",
            ),
        ),
    ),
    Chapter(
        number=6,
        title="Sim-to-Real",
        short="Entraîner le ML sur des données synthétiques",
        theory_key="rl_vs_mlp",
        steps=(
            ChapterStep(
                kind="sim", sim_key="sim_to_real",
                text=(
                    "100 000 trajectoires simulées → le ML prédit presque parfaitement. "
                    "La simulation remplace le laboratoire — si le modèle physique est bon."
                ),
            ),
        ),
    ),
)
