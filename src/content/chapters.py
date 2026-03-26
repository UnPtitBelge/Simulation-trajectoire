"""Chapters — timeline data for the normal mode.

4 chapters, one simulation each.  Presets are applied live via F1-F3.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChapterStep:
    """One simulation step within a chapter.

    kind: always "sim" (theory steps removed)
    sim_key: simulation to show
    preset: preset name to apply (None = default params)
    text: short overlay text shown during this step
    """

    kind: str  # "sim"
    text: str = ""
    sim_key: str | None = None
    preset: str | None = None


@dataclass(frozen=True)
class Chapter:
    """A chapter in the timeline."""

    number: int
    title: str
    short: str  # one-line summary for the timeline bar
    theory_key: str  # kept for reference
    steps: tuple[ChapterStep, ...] = field(default_factory=tuple)


# ── 4 chapters — one per simulation ──────────────────────────────────────────

CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        number=1,
        title="MCU — Mouvement Circulaire Uniforme",
        short="Modèle prescriptif : position calculée, zéro erreur numérique",
        theory_key="mcu",
        steps=(
            ChapterStep(kind="sim", sim_key="mcu"),
        ),
    ),
    Chapter(
        number=2,
        title="Cône — Newton + frottement de Coulomb",
        short="Orbites en rosette, spirale vers le centre",
        theory_key="newton_cone",
        steps=(
            ChapterStep(kind="sim", sim_key="cone"),
        ),
    ),
    Chapter(
        number=3,
        title="Machine Learning — données réelles",
        short="Apprendre depuis des trajectoires filmées",
        theory_key="machine_learning",
        steps=(
            ChapterStep(kind="sim", sim_key="ml"),
        ),
    ),
    Chapter(
        number=4,
        title="Sim-to-Real",
        short="Entraîner le ML sur des données synthétiques",
        theory_key="rl_vs_mlp",
        steps=(
            ChapterStep(kind="sim", sim_key="sim_to_real"),
        ),
    ),
)
