from __future__ import annotations

import plotly.graph_objects as go

BAR_COLOR = "#3987e5"
GRIDLINE_COLOR = "#2c2c2a"
TEXT_COLOR = "#ffffff"
MUTED_COLOR = "#c3c2b7"


def _prettify(label: str) -> str:
    return label.replace("_", " ").title()


def horizontal_bar_chart(
    data: dict,
    title: str,
    order: list[str] | None = None,
    prettify_labels: bool = True,
):
    """A single-hue horizontal bar chart for one series over nominal/ordinal categories."""

    if not data:
        return None

    if order:
        items = [(key, data.get(key, 0)) for key in order if key in data]
    else:
        items = sorted(data.items(), key=lambda item: item[1], reverse=True)

    labels = [_prettify(key) if prettify_labels else key for key, _ in items]
    values = [value for _, value in items]
    tick_step = max(1, round(max(values) / 6))

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=BAR_COLOR),
            text=values,
            textposition="outside",
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_COLOR),
        margin=dict(l=10, r=30, t=40, b=10),
        xaxis=dict(
            gridcolor=GRIDLINE_COLOR,
            zerolinecolor=GRIDLINE_COLOR,
            color=MUTED_COLOR,
            tick0=0,
            dtick=tick_step,
        ),
        yaxis=dict(color=MUTED_COLOR, autorange="reversed"),
        height=max(220, 60 * len(labels) + 80),
        showlegend=False,
    )

    return fig
