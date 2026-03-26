"""Core content package - educational content for the application."""

from src.core.content.chapters import CHAPTERS, Chapter, ChapterStep
from src.core.content.simulations import (
    APP_TITLE,
    SIM,
    WELCOME_INTRO,
    WELCOME_SUBTITLE,
    WELCOME_TITLE,
)
from src.core.content.theory import GLOSSARY, THEORY

__all__ = [
    "APP_TITLE",
    "WELCOME_TITLE",
    "WELCOME_SUBTITLE",
    "WELCOME_INTRO",
    "SIM",
    "THEORY",
    "GLOSSARY",
    "CHAPTERS",
    "Chapter",
    "ChapterStep",
]
