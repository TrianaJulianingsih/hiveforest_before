import base64
import io

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

# HiveForest brand colors, taken from main.html css vars
HIVE_PRIMARY = "#1a472a"
HIVE_SECONDARY = "#8B7355"
HIVE_ACCENT = "#D4A017"
HIVE_GOLD = "#FFC107"
HIVE_DARK = "#0d2818"
HIVE_FOREST = "#2d5a27"
HIVE_WISDOM = "#c9a03d"
HIVE_HONEY = "#FFD700"

PIE_COLORS = [
    HIVE_PRIMARY,
    HIVE_GOLD,
    HIVE_FOREST,
    HIVE_ACCENT,
    HIVE_SECONDARY,
    HIVE_WISDOM,
    HIVE_HONEY,
    HIVE_DARK,
    "#6b8e23",
    "#a0522d",
]


# Short axis label, e.g. 1.2 B
def _short_number(value, pos=None):
    value = float(value)
    if abs(value) >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.1f} T"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f} B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f} M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f} K"
    return f"{value:.0f}"


# Cut long label so chart stays readable
def _trim(text, length=22):
    text = str(text)
    if len(text) <= length:
        return text
    return text[: length - 3] + "..."


# New blank figure, Agg canvas so it never needs a GUI
def _new_figure(width=10, height=4):
    fig = Figure(figsize=(width, height), dpi=100)
    FigureCanvasAgg(fig)
    fig.patch.set_facecolor("white")
    return fig


# Common axis styling
def _style_axis(ax, title="", xlabel="", ylabel=""):
    ax.set_title(title, fontsize=13, fontweight="bold", color=HIVE_DARK, pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=HIVE_SECONDARY)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=HIVE_SECONDARY)
    ax.tick_params(labelsize=8, colors=HIVE_DARK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#dddddd")
    ax.spines["bottom"].set_color("#dddddd")
    ax.set_axisbelow(True)


# Figure to base64 png string, ready for img src
def _to_base64(fig):
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    buffer.close()
    return encoded


# Placeholder image when there is no data
def build_empty_chart(message="No data available"):
    fig = _new_figure(10, 3)
    ax = fig.subplots()
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        fontsize=12,
        color=HIVE_SECONDARY,
    )
    ax.axis("off")
    return _to_base64(fig)

# Distinct colors for multi line charts
SERIES_COLORS = [
    HIVE_PRIMARY, HIVE_ACCENT, HIVE_FOREST, "#4682b4", "#a0522d",
    "#800080", "#008080", "#b8860b", "#cd5c5c", "#483d8b",
    "#556b2f", "#8b0000", "#2f4f4f", "#6b8e23", "#708090",
    "#c71585", "#20b2aa", "#ff8c00", "#5f9ea0", "#9932cc",
]


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: build_multi_line_chart                              ║
# ║  Type: Chart builder                                       ║
# ║  Purpose: One colored line per series, legend on the right ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\utils\chart_utils.py                 ║
# ║  Created: Aug/21-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
def build_multi_line_chart(x_labels, series, title="", ylabel=""):
    if not x_labels or not series:
        return build_empty_chart()

    # Wider when there are many periods, taller when many lines
    width = max(11.0, min(22.0, 0.6 * len(x_labels) + 7.0))
    height = max(4.5, min(9.0, 0.22 * len(series) + 4.0))
    fig = _new_figure(width, height)
    ax = fig.subplots()
    positions = list(range(len(x_labels)))

    for index, item in enumerate(series):
        others = item.get("is_others")
        ax.plot(
            positions,
            item["values"],
            marker="o",
            markersize=3 if others else 4,
            linewidth=1.6 if others else 2,
            # Others is a leftover bucket, keep it visually quiet
            color="#adb5bd" if others else SERIES_COLORS[index % len(SERIES_COLORS)],
            linestyle="--" if others else "-",
            label=_trim(item["label"], 30),
        )

    ax.set_xticks(positions)
    ax.set_xticklabels(
        [_trim(x, 12) for x in x_labels],
        rotation=45 if len(x_labels) > 8 else 0,
        ha="right" if len(x_labels) > 8 else "center",
    )
    ax.yaxis.set_major_formatter(FuncFormatter(_short_number))
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        fontsize=8,
        frameon=False,
    )
    _style_axis(ax, title, "", ylabel)
    return _to_base64(fig)



# ╔════════════════════════════════════════════════════════════╗
# ║  Name: build_donut_chart                                   ║
# ║  Type: Chart builder                                       ║
# ║  Purpose: Composition share with grand total in the middle ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\utils\chart_utils.py                 ║
# ║  Created: Aug/21-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
def build_donut_chart(labels, values, title="", center_label=""):
    if not labels or sum(values) <= 0:
        return build_empty_chart()

    total = float(sum(values))
    fig = _new_figure(11, 6)
    ax = fig.subplots()

    wedges, _texts, autotexts = ax.pie(
        values,
        # Hide the label on thin slices, they overlap otherwise
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 3 else "",
        startangle=90,
        counterclock=False,
        colors=SERIES_COLORS[: len(values)],
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.5},
        pctdistance=0.79,
    )
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_color("white")
        autotext.set_fontweight("bold")

    ax.text(0, 0.08, _short_number(total), ha="center", va="center",
            fontsize=16, fontweight="bold", color=HIVE_DARK)
    ax.text(0, -0.12, center_label or "TOTAL", ha="center", va="center",
            fontsize=8, color=HIVE_SECONDARY)

    legend_labels = [
        f"{_trim(label, 26)}  {value / total * 100:.1f}%"
        for label, value in zip(labels, values)
    ]
    ax.legend(wedges, legend_labels, loc="center left",
              bbox_to_anchor=(1.0, 0.5), fontsize=8, frameon=False)

    ax.set_title(title, fontsize=13, fontweight="bold", color=HIVE_DARK, pad=14)
    ax.axis("equal")
    return _to_base64(fig)



# ╔════════════════════════════════════════════════════════════╗
# ║  Name: build_grouped_bar_chart                             ║
# ║  Type: Chart builder                                       ║
# ║  Purpose: Two bars per category, before against after      ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\utils\chart_utils.py                 ║
# ║  Created: Aug/26-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
def build_grouped_bar_chart(
    labels, before, after, label_before, label_after,
    title="", ylabel="", growth_labels=None
):
    if not labels:
        return build_empty_chart()

    # Wider when there are many categories
    width = max(10.0, min(22.0, 1.1 * len(labels) + 4.0))
    fig = _new_figure(width, 5.4)
    ax = fig.subplots()

    positions = list(range(len(labels)))
    bar_width = 0.36
    left = [p - bar_width / 2 for p in positions]
    right = [p + bar_width / 2 for p in positions]

    bars_a = ax.bar(left, before, bar_width, color=HIVE_PRIMARY, label=label_before)
    bars_b = ax.bar(right, after, bar_width, color=HIVE_ACCENT, label=label_after)

    # Value captions tilt so neighbouring bars never collide
    if len(labels) <= 12:
        for group in (bars_a, bars_b):
            for bar in group:
                height = bar.get_height()
                if height <= 0:
                    continue
                ax.annotate(
                    _short_number(height),
                    (bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="left",
                    va="bottom",
                    rotation=55,
                    fontsize=6.5,
                    color=HIVE_SECONDARY,
                )

    # Growth caption sits above the taller bar of each pair
    peak = max(list(before) + list(after) + [0])
    if peak > 0:
        # Extra headroom for the tilted value captions and the growth line
        ax.set_ylim(0, peak * 1.30)
    if growth_labels and peak > 0:
        for index, text in enumerate(growth_labels):
            if not text:
                continue
            color = HIVE_SECONDARY
            if text.startswith("+"):
                color = HIVE_PRIMARY
            elif text.startswith("-"):
                color = "#b02a37"
            ax.annotate(
                text,
                (positions[index], max(before[index], after[index]) + peak * 0.17),
                ha="center",
                fontsize=8,
                fontweight="bold",
                color=color,
            )

    ax.set_xticks(positions)
    ax.set_xticklabels(
        [_trim(x, 18) for x in labels],
        rotation=35 if len(labels) > 6 else 0,
        ha="right" if len(labels) > 6 else "center",
        fontsize=8,
    )
    ax.yaxis.set_major_formatter(FuncFormatter(_short_number))
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    # Legend below the plot so it can never sit on top of a bar
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        fontsize=9,
        frameon=False,
    )
    _style_axis(ax, title, "", ylabel)
    return _to_base64(fig)