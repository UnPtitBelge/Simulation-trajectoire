"""Dashboard widgets for simulation comparison and control."""

from src.view.dashboard._comparison_view import ComparisonView
from src.view.dashboard.metrics_panel import MetricsPanel
from src.view.dashboard.sim_dashboard import SimDashboard
from src.view.dashboard.sim_to_real_view import SimToRealView

__all__ = [
    "SimDashboard",
    "MetricsPanel",
    "ComparisonView",
    "SimToRealView",
]
