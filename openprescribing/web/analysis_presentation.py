from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass
class AnalysisPresentation:
    """Represents configuration for displaying a prescribing analysis.

    See docstring to Analysis class for discussion about what belongs here vs on
    Analysis.
    """

    chart_type: ChartType

    @classmethod
    def from_params(cls, params):
        """Build an AnalysisPresentation from URL query parameters."""

        try:
            chart_type = ChartType(params.get("chart_type", ChartType.DECILES))
        except ValueError:
            chart_type = ChartType.DECILES
        return AnalysisPresentation(chart_type=chart_type)


class ChartType(StrEnum):
    DECILES = "deciles"
    ALL_ORGS_LINE = "all-orgs-line"
    ALL_ORGS_DOTS = "all-orgs-dots"
