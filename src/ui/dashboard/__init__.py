"""Dashboard widgets for simulation comparison and control."""

from src.ui.dashboard._comparison_view import ComparisonView
from src.ui.dashboard.metrics_panel import MetricsPanel
from src.ui.dashboard.sim_dashboard import SimDashboard
from src.ui.dashboard.sim_to_real_view import SimToRealView

__all__ = [
    "SimDashboard",
    "MetricsPanel",
    "ComparisonView",
    "SimToRealView",
]
