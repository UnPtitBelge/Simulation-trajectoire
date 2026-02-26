from __future__ import annotations

# Spacing between navbar items (uses Bootstrap gap utility)
NAV_GAP_CLASS: str = "gap-2"

# Horizontal padding for the navbar container (px = padding-inline)
NAVBAR_PADDING_CLASS: str = "px-3"

# Right-aligned, flex container for controls (e.g., color mode switch)
# - ms-auto pushes the container to the right within a flex row
# - d-flex enables flexbox
# - align-items-center vertically centers children
# - gap-2 adds space between children
NAV_RIGHT_UTILS_CLASS: str = "ms-auto d-flex align-items-center gap-2"

__all__ = [
    "NAV_GAP_CLASS",
    "NAVBAR_PADDING_CLASS",
    "NAV_RIGHT_UTILS_CLASS",
]
