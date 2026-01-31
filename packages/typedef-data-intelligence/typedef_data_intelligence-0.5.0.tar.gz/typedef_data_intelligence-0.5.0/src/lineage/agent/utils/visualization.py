"""Safe visualization tools for data analyst agent."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
import plotly.io as pio

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Supported chart types."""

    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    AREA = "area"
    TABLE = "table"


@dataclass
class ChartSpec:
    """Declarative chart specification - no code execution."""

    chart_type: ChartType
    title: str
    data: List[Dict[str, Any]]  # List of dicts with consistent keys
    x_column: Optional[str] = None  # Column name for x-axis (not needed for pie)
    y_columns: Optional[List[str]] = None  # Column name(s) for y-axis
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    legend: bool = True
    stacked: bool = False
    color_column: Optional[str] = None  # For coloring by category
    figsize: tuple[int, int] = (10, 6)


class SafeVisualization:
    """Generate charts from declarative specifications (no code execution)."""

    @staticmethod
    def create_chart_from_plotly_json(plotly_json: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """Create a chart directly from Plotly JSON specification.

        Args:
            plotly_json: Plotly figure specification as a dict (data + layout)
            output_path: Where to save the chart (defaults to temp file)

        Returns:
            Path to the saved chart image

        Example plotly_json:
            {
                "data": [
                    {
                        "type": "bar",
                        "x": ["Q1", "Q2", "Q3", "Q4"],
                        "y": [100, 150, 125, 175],
                        "name": "Revenue"
                    }
                ],
                "layout": {
                    "title": "Quarterly Revenue",
                    "xaxis": {"title": "Quarter"},
                    "yaxis": {"title": "Revenue ($)"}
                }
            }
        """
        # Create figure from JSON
        fig = go.Figure(plotly_json)

        # Save to file
        if output_path is None:
            import tempfile
            import os

            fd, temp_path = tempfile.mkstemp(suffix=".png", prefix="chart_")
            os.close(fd)
            output_path = Path(temp_path)

        # Thread-safe write using kaleido
        pio.write_image(fig, output_path, format="png")

        logger.info(f"Chart saved to {output_path}")
        return output_path

    @staticmethod
    def create_chart(spec: ChartSpec, output_path: Optional[Path] = None) -> Path:
        """Create a chart from a declarative specification using Plotly.

        Args:
            spec: Chart specification
            output_path: Where to save the chart (defaults to temp file)

        Returns:
            Path to the saved chart image

        Raises:
            ValueError: If chart spec is invalid
        """
        # Validate spec
        if not spec.data:
            raise ValueError("Chart data cannot be empty")

        if spec.chart_type not in (ChartType.PIE, ChartType.TABLE) and not spec.x_column:
            raise ValueError(f"x_column required for {spec.chart_type} charts")

        if spec.chart_type not in (ChartType.PIE, ChartType.TABLE) and not spec.y_columns:
            raise ValueError(f"y_columns required for {spec.chart_type} charts")

        # Extract data
        try:
            if spec.chart_type == ChartType.PIE:
                values = [row.get(spec.y_columns[0], 0) for row in spec.data]
                labels = [row.get(spec.x_column, "Unknown") for row in spec.data]
            else:
                x_values = [row.get(spec.x_column) for row in spec.data]
                y_data = {col: [row.get(col, 0) for row in spec.data] for col in spec.y_columns}
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid data structure: {e}") from e

        # Create figure using Plotly
        fig = go.Figure()

        # Render chart based on type
        if spec.chart_type == ChartType.BAR:
            for col in spec.y_columns:
                fig.add_trace(
                    go.Bar(
                        x=x_values,
                        y=y_data[col],
                        name=col,
                    )
                )
            if spec.stacked:
                fig.update_layout(barmode="stack")
            else:
                fig.update_layout(barmode="group")

        elif spec.chart_type == ChartType.HORIZONTAL_BAR:
            for col in spec.y_columns:
                fig.add_trace(
                    go.Bar(
                        x=y_data[col],
                        y=x_values,
                        name=col,
                        orientation="h",
                    )
                )
            if spec.stacked:
                fig.update_layout(barmode="stack")
            else:
                fig.update_layout(barmode="group")

        elif spec.chart_type == ChartType.LINE:
            for col in spec.y_columns:
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_data[col],
                        mode="lines+markers",
                        name=col,
                    )
                )

        elif spec.chart_type == ChartType.SCATTER:
            for col in spec.y_columns:
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_data[col],
                        mode="markers",
                        name=col,
                        marker=dict(opacity=0.6),
                    )
                )

        elif spec.chart_type == ChartType.PIE:
            fig.add_trace(
                go.Pie(
                    values=values,
                    labels=labels,
                    textposition="auto",
                    textinfo="label+percent",
                )
            )

        elif spec.chart_type == ChartType.AREA:
            for col in spec.y_columns:
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_data[col],
                        mode="lines",
                        name=col,
                        fill="tonexty" if spec.stacked else "tozeroy",
                        fillcolor=None,
                        opacity=0.7 if spec.stacked else 0.3,
                    )
                )

        elif spec.chart_type == ChartType.TABLE:
            # Extract all columns from data
            if not spec.data:
                raise ValueError("Table data cannot be empty")

            # Get all unique column names from the data
            all_columns = list(spec.data[0].keys()) if spec.data else []

            # Build column data
            column_data = {col: [row.get(col, "") for row in spec.data] for col in all_columns}

            fig.add_trace(
                go.Table(
                    header=dict(
                        values=list(all_columns),
                        fill_color="paleturquoise",
                        align="left",
                        font=dict(size=12, color="black")
                    ),
                    cells=dict(
                        values=list(column_data.values()),
                        fill_color="lavender",
                        align="left",
                        font=dict(size=11)
                    )
                )
            )

        # Update layout
        layout_config = {
            "title": {"text": spec.title, "font": {"size": 16}},
            "showlegend": spec.legend and spec.y_columns and len(spec.y_columns) > 1,
            "width": spec.figsize[0] * 100,  # Convert to pixels (approx)
            "height": spec.figsize[1] * 100,
        }

        if spec.chart_type not in (ChartType.PIE, ChartType.TABLE):
            layout_config["xaxis"] = {"title": spec.x_label or ""}
            layout_config["yaxis"] = {"title": spec.y_label or ""}

            # Format large numbers with commas
            if spec.chart_type != ChartType.HORIZONTAL_BAR:
                layout_config["yaxis"]["tickformat"] = ",d"
            else:
                layout_config["xaxis"]["tickformat"] = ",d"

        fig.update_layout(**layout_config)

        # Save to file
        if output_path is None:
            import tempfile
            import os

            fd, temp_path = tempfile.mkstemp(suffix=".png", prefix="chart_")
            os.close(fd)
            output_path = Path(temp_path)

        # Thread-safe write using kaleido
        pio.write_image(fig, output_path, format="png", width=spec.figsize[0] * 100, height=spec.figsize[1] * 100)

        logger.info(f"Chart saved to {output_path}")
        return output_path


def create_chart_from_query_result(
    chart_type: str,
    title: str,
    data: List[List[Any]],
    columns: List[str],
    x_column: Optional[str] = None,
    y_columns: Optional[List[str]] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    **kwargs,
) -> Path:
    """Helper to create a chart from query results.

    Args:
        chart_type: Type of chart (bar, line, scatter, pie, area, horizontal_bar, table)
        title: Chart title
        data: Query result rows
        columns: Query result column names
        x_column: Name of column to use for x-axis (not needed for table)
        y_columns: Names of columns to plot on y-axis (not needed for table)
        x_label: Label for x-axis
        y_label: Label for y-axis
        **kwargs: Additional ChartSpec parameters

    Returns:
        Path to saved chart image
    """
    # Convert rows to list of dicts
    data_dicts = [dict(zip(columns, row)) for row in data]

    spec = ChartSpec(
        chart_type=ChartType(chart_type),
        title=title,
        data=data_dicts,
        x_column=x_column,
        y_columns=y_columns or [],
        x_label=x_label,
        y_label=y_label,
        **kwargs,
    )

    viz = SafeVisualization()
    return viz.create_chart(spec)
