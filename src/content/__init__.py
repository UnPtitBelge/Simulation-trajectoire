"""Content module — chapters, theory, and simulation metadata."""

from .chapters import CHAPTERS, Chapter, ChapterStep
from .simulations import SIM, WELCOME_INTRO, WELCOME_SUBTITLE, WELCOME_TITLE
from .theory.theory import GLOSSARY, THEORY

APP_TITLE = "Simulation Trajectoire"


__all__ = [
    "APP_TITLE",
    "CHAPTERS",
    "Chapter",
    "ChapterStep",
    "SIM",
    "WELCOME_INTRO",
    "WELCOME_SUBTITLE",
    "WELCOME_TITLE",
    "GLOSSARY",
    "THEORY",
]
