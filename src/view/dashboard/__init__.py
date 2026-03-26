"""Dashboard widgets for simulation comparison and control."""

from src.ui.views.dashboard._comparison_view import ComparisonView
from src.ui.views.dashboard.metrics_panel import MetricsPanel
from src.ui.views.dashboard.sim_dashboard import SimDashboard
from src.ui.views.dashboard.sim_to_real_view import SimToRealView

__all__ = [
    "SimDashboard",
    "MetricsPanel",
    "ComparisonView",
    "SimToRealView",
]
