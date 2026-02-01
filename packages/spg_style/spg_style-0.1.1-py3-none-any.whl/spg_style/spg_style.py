"""
S&P Global EDP Visual Style Guide Implementation (Python/Matplotlib)
====================================================================
Last Updated: Jan 2026
Reference: S&P Global EDP Visual Style Guide (Jan 2026 PDF)

Description:
    This module provides a strict implementation of the S&P Global Editorial,
    Design & Publishing (EDP) standards for data visualization.

    It enforces rules regarding:
    - Colors (Full palette, Standard Light/Dark modes, Sentiment)
    - Typography (Akkurat LL / Arial)
    - Layout (Spines, Ticks, Gridlines)
    - Specific Chart Logic (Forecast tints, Stacked totals, Direct labeling)

Usage:
    import spg_style as spg

    # Initialize (sets global matplotlib params)
    style = spg.SpglobalStyle(theme='light')

    # Plot standard matplotlib chart
    fig, ax = plt.subplots(figsize=spg.get_edp_figsize())
    bars = ax.bar(...)

    # Apply strict EDP styling
    style.style_bar_single(ax, bars)
    style.add_footnotes(fig, source="S&P Global Market Intelligence")
"""

import os
import datetime
from io import BytesIO
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Union

import pandas as pd

# pip install python-pptx
# from pptx import Presentation
# from pptx.util import Inches, Pt, Cm
# from pptx.enum.text import PP_ALIGN
# from pptx.dml.color import RGBColor

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
from matplotlib.ticker import LinearLocator, FuncFormatter

# ==============================================================================
# 1. COLOR DEFINITIONS
# Reference: Page 5 "Full palette" (Jan 2026)
# ==============================================================================

# Exact hex codes transcribed from Page 5 of the PDF.
# Level 12 is the darkest, Level 1 is the lightest.
SPG_FULL: Dict[str, Dict[int, str]] = {
    "Red": {
        12: "#240007",
        11: "#47000e",
        10: "#6b0015",
        9: "#8f001c",
        8: "#b20023",
        7: "#cc0031",
        6: "#e14542",
        5: "#eb685b",
        4: "#f38777",
        3: "#f9a495",
        2: "#fdc1b4",
        1: "#ffddd5",
    },
    "Maroon": {
        12: "#1b0400",
        11: "#360701",
        10: "#510b01",
        9: "#6b0f01",
        8: "#861202",
        7: "#a11602",
        6: "#ae3726",
        5: "#bc594a",
        4: "#c97a6e",
        3: "#d79b93",
        2: "#e4bcb7",
        1: "#f2dedb",
    },
    "Magenta": {
        12: "#1f050e",
        11: "#3e0b1b",
        10: "#5d1029",
        9: "#7b1536",
        8: "#9a1b43",
        7: "#b92051",
        6: "#c3406a",
        5: "#cd6083",
        4: "#d7809c",
        3: "#e19fb4",
        2: "#ebbfcd",
        1: "#f5dfe6",
    },
    "Purple": {
        12: "#140515",
        11: "#280b2b",
        10: "#3c1040",
        9: "#501555",
        8: "#641b6b",
        7: "#782080",
        6: "#8b4092",
        5: "#9f60a4",
        4: "#b280b6",
        3: "#c59fc9",
        2: "#d8bfdb",
        1: "#ecdfed",
    },
    "Blue": {
        12: "#000e40",
        11: "#01145f",
        10: "#011b7f",
        9: "#01229f",
        8: "#1d3baa",
        7: "#3953b4",
        6: "#566cbf",
        5: "#7284ca",
        4: "#8e9dd4",
        3: "#aab5df",
        2: "#c0c8e7",
        1: "#e3e6f4",
    },
    "Ocean": {
        12: "#001217",
        11: "#00242e",
        10: "#003745",
        9: "#00495b",
        8: "#005b72",
        7: "#006d89",
        6: "#24829a",
        5: "#4997ab",
        4: "#6cabbb",
        3: "#92c0cc",
        2: "#b6d5dd",
        1: "#dbeaee",
    },
    "Teal": {
        12: "#031a14",
        11: "#053529",
        10: "#084f3d",
        9: "#0a6951",
        8: "#0c8466",
        7: "#0f9e7a",
        6: "#31ac8d",
        5: "#54baa0",
        4: "#76c8b3",
        3: "#98d5c6",
        2: "#bae3d9",
        1: "#ddf1ec",
    },
    "Green": {
        12: "#051808",
        11: "#092f10",
        10: "#0e4718",
        9: "#125e1f",
        8: "#167527",
        7: "#1b8d2f",
        6: "#3c9d4d",
        5: "#5cae6a",
        4: "#7dbe88",
        3: "#9dcea6",
        2: "#bedec4",
        1: "#deefe1",
    },
    "Ochre": {
        12: "#051808",
        11: "#402e0d",
        10: "#614614",
        9: "#815d1b",
        8: "#a17421",
        7: "#c18b28",
        6: "#ca9c47",
        5: "#d3ac65",
        4: "#dcbd84",
        3: "#e4cda3",
        2: "#eddec2",
        1: "#f6eee0",
    },
    "Gold": {
        12: "#271600",
        11: "#4f2b00",
        10: "#764100",
        9: "#9d5700",
        8: "#c56c00",
        7: "#DC7900",
        6: "#ef9424",
        5: "#f1a649",
        4: "#f4b86d",
        3: "#f7c992",
        2: "#fadbb6",
        1: "#fceddb",
    },
    "Orange": {
        12: "#220b00",
        11: "#431600",
        10: "#652100",
        9: "#862b00",
        8: "#a73600",
        7: "#c94100",
        6: "#d15c24",
        5: "#d87749",
        4: "#e0926d",
        3: "#e8ae92",
        2: "#f0c9b6",
        1: "#f7e4db",
    },
    "Brown": {
        12: "#20180b",
        11: "#32291c",
        10: "#463b2c",
        9: "#5b4f3d",
        8: "#71634e",
        7: "#887760",
        6: "#9e8d73",
        5: "#af9e86",
        4: "#c0b09a",
        3: "#d0c2ae",
        2: "#e1d4c2",
        1: "#f2e7d7",
    },
    "Gray": {
        12: "#0a0a0a",
        11: "#1f1f1f",
        10: "#333333",
        9: "#595959",
        8: "#808184",
        7: "#929497",
        6: "#a6a8ab",
        5: "#bbbdbf",
        4: "#d0d2d3",
        3: "#e6e7e8",
        2: "#f1f1f2",
        1: "#ffffff",
    },
}

# --- Functional Constants ---
# Reference: Page 4 "Positive/negative; highlights and grays"
# UPDATED for 2026 Guidelines
SENTIMENT = {
    "positive": SPG_FULL["Green"][8],  # "Positive/Gain" - Page 4
    "somewhat_positive": SPG_FULL["Green"][3],  # "Somewhat Positive" - Page 4
    "neutral": SPG_FULL["Gray"][5],  # "Neutral/No change"
    "neutral_alt": SPG_FULL["Ocean"][
        5
    ],  # "Use Ocean 5 for Neutral" if Gray is background
    "somewhat_negative": SPG_FULL["Maroon"][3],  # "Somewhat Negative" - Page 4
    "negative": SPG_FULL["Red"][8],  # "Negative/Loss" - Page 4
}

# Reference: Page 3 "Standard - Light mode"
STANDARD_LIGHT_MODE_PALETTE = [
    SPG_FULL["Ocean"][7],
    SPG_FULL["Gold"][7],
    SPG_FULL["Magenta"][7],
    SPG_FULL["Purple"][9],
    SPG_FULL["Teal"][7],
    SPG_FULL["Ocean"][9],
    SPG_FULL["Orange"][7],
    SPG_FULL["Blue"][8],
    SPG_FULL["Magenta"][5],
    SPG_FULL["Green"][9],
    SPG_FULL["Gray"][7],
    SPG_FULL["Purple"][7],
    SPG_FULL["Blue"][5],
    SPG_FULL["Gold"][9],
    SPG_FULL["Purple"][4],
    SPG_FULL["Blue"][6],
    SPG_FULL["Ocean"][4],
    SPG_FULL["Ochre"][7],
    SPG_FULL["Green"][6],
    SPG_FULL["Maroon"][9],
]

# Reference: Page 3 "Standard - Dark mode" (Background: Gray 12)
STANDARD_DARK_MODE_PALETTE = [
    SPG_FULL["Ocean"][6],
    SPG_FULL["Gold"][5],
    SPG_FULL["Magenta"][5],
    SPG_FULL["Purple"][5],
    SPG_FULL["Teal"][5],
    SPG_FULL["Ocean"][4],
    SPG_FULL["Orange"][5],
    SPG_FULL["Blue"][6],
    SPG_FULL["Magenta"][3],
    SPG_FULL["Green"][6],
    SPG_FULL["Gray"][5],
    SPG_FULL["Purple"][4],
    SPG_FULL["Blue"][2],
    SPG_FULL["Gold"][3],
    SPG_FULL["Purple"][1],
    SPG_FULL["Blue"][4],
    SPG_FULL["Ocean"][2],
    SPG_FULL["Ochre"][5],
    SPG_FULL["Green"][3],
    SPG_FULL["Maroon"][5],
]

# Helper to reverse look up colors for the tinting function
COLOR_LOOKUP = {}
for fam, levels in SPG_FULL.items():
    for lvl, hex_val in levels.items():
        COLOR_LOOKUP[hex_val.lower()] = (fam, lvl)

# ==============================================================================
# 2. UTILITY FUNCTIONS
# ==============================================================================


def get_forecast_color(base_hex: str) -> str:
    """
    Calculates the tint for forecast data.

    Reference: Page 8f (Excel Charts > Formatting)
    "Bar tinting: For bars that don’t fit the pattern (ie., forecasts),
    tint them a lighter shade (level 2 lighter tint for a level 7 main color)."
    """
    base_hex = base_hex.lower()
    if base_hex in COLOR_LOOKUP:
        fam, lvl = COLOR_LOOKUP[base_hex]
        new_lvl = max(1, lvl - 2)  # Ensure we don't go below Level 1
        return SPG_FULL[fam][new_lvl]
    return base_hex  # Return original if not found in EDP palette


def get_monochromatic_palette(color_family: str, steps: int) -> List[str]:
    """
    Returns a strict monochromatic palette.

    Reference: Page 4 "Monochromatic" (Jan 2026 update)
    2 classes: Level 7, 3
    3 classes: Level 11, 7, 3
    4 classes: Level 12, 9, 6, 3
    5 classes: Level 12, 9, 7, 5, 3
    """
    rules = {2: [7, 3], 3: [11, 7, 3], 4: [12, 9, 6, 3], 5: [12, 9, 7, 5, 3]}
    if steps not in rules:
        raise ValueError("Monochromatic steps must be 2, 3, 4, or 5 (Ref: Page 4)")

    return [SPG_FULL[color_family][lvl] for lvl in rules[steps]]


def get_edp_figsize(
    width: str = "full", height: str = "full", target: str = "ppt"
) -> Tuple[float, float]:
    """
    Returns (width, height) in inches based on Page 21 of the S&P Global Style Guide.

    Parameters:
    -----------
    width : str
        The width fraction.
        Options: 'full', '3/4', '2/3', '1/2', '1/3'.
        (Note: '3/4' and '1/3' are only available for 'ppt' target).

    height : str
        The height fraction.
        Options:
            - For 'report': 'max', '2/3', '1/2', '1/3'
            - For 'ppt': 'std' (Standard), 'full'

    target : str
        The output medium. Options: 'report' (default) or 'ppt'.
        - 'report': Maps to "Word/InDesign graphic sizes (Digital)"
        - 'ppt': Maps to "PowerPoint graphic sizes (16 x 9)"

    Returns:
    --------
    Tuple[float, float] : (width_inches, height_inches)

    Usage:
    ------
    # Standard Report Chart (Full width, half height) -> (7.5, 4.6)
    fig_size = spg.get_edp_figsize(width="full", height="1/2")

    # Side-by-side Report Chart (Half width, 1/3 height) -> (3.6, 3.5)
    fig_size = spg.get_edp_figsize(width="1/2", height="1/3")

    # Standard PowerPoint Slide Chart -> (12.1, 5.4)
    fig_size = spg.get_edp_figsize(width="full", height="std", target="ppt")
    """

    # Normalize inputs
    w_key = str(width).lower()
    h_key = str(height).lower()
    t_key = str(target).lower()

    # Reference: Page 21 - "Word/InDesign graphic sizes" (Digital Column)
    report_specs = {
        "width": {"full": 7.5, "2/3": 4.95, "1/2": 3.6},
        "height": {
            "max": 9.2,  # "Maximum height Reports"
            "2/3": 6.2,  # "2/3 height Reports"
            "1/2": 4.6,  # "1/2 height Reports"
            "1/3": 3.5,  # "1/3 height Reports"
        },
    }

    # Reference: Page 21 - "PowerPoint graphic sizes" (16 x 9 Template)
    # Using the "With source" dimensions as Matplotlib usually includes footer
    ppt_specs = {
        "width": {"full": 12.1, "3/4": 9.08, "2/3": 7.8, "1/2": 5.5, "1/3": 3.5},
        "height": {
            "std": 5.4,  # "Standard height (STD) With source"
            "full": 6.4,  # "Full height With source"
        },
    }

    # Select Context
    specs = ppt_specs if t_key == "ppt" else report_specs

    # Retrieve Dimensions
    w_val = specs["width"].get(w_key)
    h_val = specs["height"].get(h_key)

    # Error Handling with defaults
    if w_val is None:
        print(
            f"Warning: Width '{width}' not valid for target '{target}'. Defaulting to 'full'."
        )
        w_val = specs["width"]["full"]

    if h_val is None:
        # Set intelligent defaults based on target
        default_h = "std" if t_key == "ppt" else "1/2"
        print(
            f"Warning: Height '{height}' not valid for target '{target}'. Defaulting to '{default_h}'."
        )
        h_val = specs["height"][default_h]

    return (w_val, h_val)


def edp_date_formatter() -> FuncFormatter:
    """
    Returns a Matplotlib Formatter for dates.

    Reference: Page 7 "Date formats > Exceptions"
    "When spacing and consistency are important considerations in a visual,
    you may use these three-letter forms without a period."

    Format: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
    """

    def _formatter(x, pos):
        dt = mdates.num2date(x)
        # Use standard 3-letter abbreviation with NO dot (Jan, Sep)
        # This matches the "Exceptions" column on Page 7.
        return dt.strftime("%b")

    return FuncFormatter(_formatter)


def ensure_contrast(bg_hex: str) -> str:
    """
    Reference: Page 3 "Accessibility"
    "minimum contrast ratios required for graphics (3:1) and text (4.5:1)."
    """
    try:
        r, g, b = mcolors.to_rgb(bg_hex)
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return "#000000" if lum > 0.55 else "#ffffff"
    except:
        return "#000000"


# ==============================================================================
# 3. MAIN STYLE CLASS
# ==============================================================================


@dataclass
class SpglobalStyle:
    """
    S&P Global EDP Style Controller (Jan 2026 Standards).
    """

    font_family: str = "Arial"  # Fallback (Akkurat LL is standard but non-system)
    font_size: float = 10
    title_font_size: float = 12
    theme: str = "light"  # 'light' or 'dark' (Page 3)

    palette: List[str] = field(init=False)

    def __post_init__(self):
        # Set palette based on Page 3 "Standard"
        self.palette = (
            STANDARD_DARK_MODE_PALETTE[:]
            if self.theme == "dark"
            else STANDARD_LIGHT_MODE_PALETTE[:]
        )
        self._configure_fonts()
        self.set_rc_params()

    def _configure_fonts(self):
        """
        Reference: Page 6 "Fonts"
        "Title 2023 Akkurat LL Bold... Subtitle 2023 Akkurat LL Light"
        """
        try:
            # Check if font is installed in system
            fm.findfont("Akkurat LL", fallback_to_default=False)
            self.font_family = "Akkurat LL"
        except:
            # Fallback
            pass

    def set_rc_params(self):
        """
        Applies Global Matplotlib Settings.

        Reference: Page 8 "Excel charts > Formatting"
        """
        # Colors mapped from Gray palette
        gray_12 = SPG_FULL["Gray"][12]  # Black equivalent
        gray_6 = SPG_FULL["Gray"][6]  # "gray darker 35%" approx
        gray_4 = SPG_FULL["Gray"][4]  # "gray darker 15%" approx (Gridlines)
        gray_2 = SPG_FULL["Gray"][2]  # Dark mode lines
        white = SPG_FULL["Gray"][1]

        plt.rcParams.update(
            {
                # Color Cycle
                "axes.prop_cycle": plt.cycler(color=self.palette),
                # Spines (Page 8b "Axis: category axis line 0.75 pt, gray darker 35%")
                "axes.spines.top": False,
                "axes.spines.right": False,
                "axes.spines.bottom": True,
                "axes.spines.left": True,  # Explicitly shown in Page 8 example
                "axes.linewidth": 0.75,
                # Ticks (Page 8b "No tick marks")
                "xtick.major.size": 0,
                "ytick.major.size": 0,
                "axes.labelpad": 8,
                # Grid (Page 8d "Gridlines: 0.75 pt, gray darker 15%")
                "axes.grid": False,  # Default off per Page 8 (turn on if needed)
                "grid.linewidth": 0.75,
                # Typography (Page 6 & 8g)
                "font.family": self.font_family,
                "font.size": self.font_size,
                "axes.titlesize": self.title_font_size,
                "axes.titleweight": "bold",
                "axes.titlelocation": "left",
                # Legend (Page 10e "Legend position: Align to the top")
                "legend.frameon": False,
                "legend.title_fontsize": 0,
                "legend.fontsize": self.font_size,
            }
        )

        # Theme Handling
        if self.theme == "dark":
            plt.rcParams.update(
                {
                    "axes.facecolor": gray_12,
                    "figure.facecolor": gray_12,
                    "axes.edgecolor": gray_2,
                    "grid.color": gray_4,  # Lighter gray for grid in dark mode
                    "text.color": gray_2,
                    "axes.labelcolor": gray_2,
                    "xtick.color": gray_2,
                    "ytick.color": gray_2,
                }
            )
        else:
            plt.rcParams.update(
                {
                    "axes.facecolor": white,
                    "figure.facecolor": white,
                    "axes.edgecolor": gray_6,  # "Gray darker 35%"
                    "grid.color": gray_4,  # "Gray darker 15%"
                    "text.color": gray_12,
                    "axes.labelcolor": gray_12,
                    "xtick.color": gray_12,
                    "ytick.color": gray_12,
                }
            )

    # --- Helper Methods ---

    def set_unit_label(self, ax, label: str, axis="y"):
        """
        Reference: Page 13a "Dual y-axis charts > Axis titles"
        Short, unit only: on top of axis, no rotation.
        """
        if axis == "y":
            ax.set_ylabel("")
            ax.text(
                0,
                1.02,
                label,
                transform=ax.transAxes,
                ha="left",
                va="bottom",
                fontweight="normal",
                fontsize=self.font_size,
            )
        else:
            ax.set_xlabel("")
            ax.text(
                1.02,
                0,
                label,
                transform=ax.transAxes,
                ha="left",
                va="center",
                fontweight="normal",
                fontsize=self.font_size,
            )

    def set_y_unit_label(self, ax, label: str):
        self.set_unit_label(ax, label, axis="y")

    def apply_legend(self, ax, ncol: Optional[int] = None, **kwargs):
        """
        Reference: Page 10e "Legend position: Align to the top."
        """
        handles, labels = ax.get_legend_handles_labels()
        if not labels:
            return None

        # Smart column calculation
        if ncol is None:
            n_items = len(labels)
            if n_items <= 5:
                ncol = n_items
            elif n_items <= 10:
                ncol = 5
            else:
                ncol = 6

        # Position at top (y=1.02 approx)
        params = {
            "loc": "lower center",
            "bbox_to_anchor": (0.5, 1.02),
            "ncol": ncol,
            "frameon": False,
            "columnspacing": 1.0,
        }
        params.update(kwargs)
        return ax.legend(**params)

    def format_date_axis(self, ax, axis="x"):
        """Applies EDP Page 7 date formatting."""
        target = ax.xaxis if axis == "x" else ax.yaxis
        target.set_major_formatter(edp_date_formatter())

    def align_dual_axes(self, ax1, ax2):
        """Reference: Page 13b - Align gridlines for dual axes."""
        ticks = len(ax1.get_yticks())
        ax1.yaxis.set_major_locator(LinearLocator(ticks))
        ax2.yaxis.set_major_locator(LinearLocator(ticks))

    def add_footnotes(
        self,
        fig,
        source: str = "S&P Global Market Intelligence",
        date_str: Optional[str] = None,
        notes: Optional[List[str]] = None,
        rect: Optional[List[float]] = None,
    ):
        """
        Reference: Page 24 "Footnotes"
        Structure:
          As of [Date].
          Notes/Definitions.
          Source: ...
          Copyright line.
        """
        lines = []

        # 1. As of Date
        if date_str is None:
            date_str = datetime.datetime.now().strftime("%b. %d, %Y")
        lines.append(f"As of {date_str}.")

        # 2. Notes
        if notes:
            for n in notes:
                clean_n = n.strip()
                if not clean_n.endswith("."):
                    clean_n += "."
                lines.append(clean_n)

        # 3. Source
        lines.append(f"Source: {source}.")

        # 4. Copyright (Page 24 example shows 2026)
        year = datetime.date.today().year
        # If current year is before 2026, default to 2026 for template consistency if desired,
        # otherwise use dynamic year.
        year_str = str(max(year, 2026))
        lines.append(f"\u00a9 {year_str} S&P Global.")

        full_text = "\n".join(lines)

        # Layout
        if rect is None:
            # Reserve bottom 15% for footnotes
            rect = [0, 0.15, 1, 0.95]

        fig.tight_layout(rect=rect)

        t_color = SPG_FULL["Gray"][4] if self.theme == "dark" else SPG_FULL["Gray"][9]

        fig.text(
            0.01,
            0.01,
            full_text,
            ha="left",
            va="bottom",
            fontsize=7,
            fontfamily=self.font_family,
            color=t_color,
            linespacing=1.4,
        )

    # --- Chart Styling Presets ---

    def style_bar_single(
        self,
        ax,
        bars,
        decimals=1,
        is_forecast_mask: Optional[List[bool]] = None,
        show_labels=True,
        **kwargs,
    ):
        """
        Reference: Page 8 "Column charts, single series"
        Gap width: 50% (Use width=0.66 in bar plot)
        """
        ax.set_ylim(bottom=0)

        for i, rect in enumerate(bars):
            height = rect.get_height()

            # Forecast Logic (Page 8f)
            if is_forecast_mask and i < len(is_forecast_mask) and is_forecast_mask[i]:
                orig_color = mcolors.to_hex(rect.get_facecolor())
                rect.set_facecolor(get_forecast_color(orig_color))

            # Label Logic (Page 8g)
            if show_labels:
                label_color = (
                    SPG_FULL["Gray"][12]
                    if self.theme == "light"
                    else SPG_FULL["Gray"][2]
                )
                ax.annotate(
                    f"{height:.{decimals}f}",
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    color=label_color,
                    fontsize=self.font_size,
                )

        self.apply_legend(ax, ncol=1)

    def style_clustered_bar(
        self, ax, containers, decimals=1, horizontal=False, show_labels=True, **kwargs
    ):
        """
        Reference: Page 10a "Series overlap: -15%"

        To achieve -15% overlap in Matplotlib, you must manually calculate
        x-positions for your bars. This function styles them assuming they are plotted.
        """
        label_color = (
            SPG_FULL["Gray"][12] if self.theme == "light" else SPG_FULL["Gray"][2]
        )

        for container in containers:
            # Tinting for older data (Page 10c) is handled by passing correct colors to plot
            for rect in container:
                # Add labels
                if show_labels:
                    if horizontal:
                        width = rect.get_width()
                        if width > 0:
                            ax.annotate(
                                f"{width:.{decimals}f}",
                                xy=(
                                    rect.get_x() + width,
                                    rect.get_y() + rect.get_height() / 2,
                                ),
                                xytext=(3, 0),
                                textcoords="offset points",
                                ha="left",
                                va="center",
                                color=label_color,
                                fontsize=self.font_size - 1,
                            )
                    else:
                        height = rect.get_height()
                        if height > 0:
                            ax.annotate(
                                f"{height:.{decimals}f}",
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha="center",
                                va="bottom",
                                color=label_color,
                                fontsize=self.font_size - 1,
                            )

        self.apply_legend(ax)

    def style_pie_donut(
        self, ax, values, labels, hole_size=0.6, show_labels=True, **kwargs
    ):
        """
        Reference: Page 14 "Pie/donut charts"
        Hole size 50-70% (Default 0.6)
        """
        autopct = "%1.0f%%" if show_labels else None
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct=autopct,
            startangle=90,
            pctdistance=0.85,
            colors=self.palette,
            wedgeprops={"linewidth": 1, "edgecolor": "white"},
        )

        # Donut Hole
        centre_circle = plt.Circle((0, 0), hole_size, fc=plt.rcParams["axes.facecolor"])
        ax.add_artist(centre_circle)

        # Label Contrast
        if show_labels and autotexts:
            for autotext, wedge in zip(autotexts, wedges):
                autotext.set_color(
                    ensure_contrast(mcolors.to_hex(wedge.get_facecolor()))
                )
                autotext.set_fontsize(self.font_size)

        ax.axis("equal")

    def style_stacked_bar(
        self,
        ax,
        containers,
        total_labels=True,
        decimals=1,
        show_labels=True,
        horizontal=False,
        **kwargs,
    ):
        """
        Reference: Page 11 "Stacked Charts"
        - Labels centered in segments.
        - Page 11c: White text unless bar too light.
        - Page 11d: Aggregate totals bold outside end.
        """
        if horizontal:
            ax.set_xlim(left=0)
        else:
            ax.set_ylim(bottom=0)

        # Segment Labels
        if show_labels:
            for container in containers:
                for rect in container:
                    if horizontal:
                        val = rect.get_width()
                        if val > 0:
                            cx = rect.get_x() + val / 2
                            cy = rect.get_y() + rect.get_height() / 2
                            try:
                                fill_hex = mcolors.to_hex(rect.get_facecolor())
                                contrast_col = ensure_contrast(fill_hex)
                            except:
                                contrast_col = (
                                    SPG_FULL["Gray"][12]
                                    if self.theme == "light"
                                    else SPG_FULL["Gray"][2]
                                )

                            ax.text(
                                cx,
                                cy,
                                f"{val:.{decimals}f}",
                                ha="center",
                                va="center",
                                color=contrast_col,
                                fontsize=self.font_size - 1,
                            )
                    else:
                        val = rect.get_height()
                        if val > 0:  # Only label visible segments
                            cy = rect.get_y() + val / 2
                            cx = rect.get_x() + rect.get_width() / 2
                            try:
                                fill_hex = mcolors.to_hex(rect.get_facecolor())
                                contrast_col = ensure_contrast(fill_hex)
                            except:
                                contrast_col = (
                                    SPG_FULL["Gray"][12]
                                    if self.theme == "light"
                                    else SPG_FULL["Gray"][2]
                                )

                            ax.text(
                                cx,
                                cy,
                                f"{val:.{decimals}f}",
                                ha="center",
                                va="center",
                                color=contrast_col,
                                fontsize=self.font_size - 1,
                            )

        # Aggregate Totals (Page 11d)
        if total_labels:
            outer_bounds = {}
            for container in containers:
                for rect in container:
                    if horizontal:
                        # y position as key, x as bound
                        key = round(rect.get_y() + rect.get_height() / 2, 3)
                        bound = rect.get_x() + rect.get_width()
                    else:
                        # x position as key, y as bound
                        key = round(rect.get_x() + rect.get_width() / 2, 3)
                        bound = rect.get_y() + rect.get_height()

                    if key not in outer_bounds or bound > outer_bounds[key]:
                        outer_bounds[key] = bound

            t_color = (
                SPG_FULL["Gray"][12] if self.theme == "light" else SPG_FULL["Gray"][2]
            )
            for pos, bound in outer_bounds.items():
                if horizontal:
                    ax.text(
                        bound,
                        pos,
                        f"{bound:.{decimals}f}",
                        ha="left",
                        va="center",
                        fontweight="bold",
                        color=t_color,
                        fontsize=self.font_size,
                    )
                else:
                    ax.text(
                        pos,
                        bound,
                        f"{bound:.{decimals}f}",
                        ha="center",
                        va="bottom",
                        fontweight="bold",
                        color=t_color,
                        fontsize=self.font_size,
                    )

        self.apply_legend(ax)

    def style_bubble(self, ax, scatters, decimals=1, show_labels=True, **kwargs):
        """
        Reference: Page 15 "Scatter and bubble charts"
        """
        # Ensure grid is visible for scatter (Page 17 exception)
        ax.grid(True, axis="both", linestyle="--", alpha=0.3)
        self.apply_legend(ax)

    def save_figure(self, fig, filename, dpi=300):
        # Saves with bounding box tight to ensure footnotes/legends aren't cut off
        fig.savefig(filename, dpi=dpi, bbox_inches="tight", pad_inches=0.2)


if __name__ == "__main__":
    import numpy as np

    # 1. Setup
    style = SpglobalStyle(theme="light")
    # Use standard 1-chart size (Reference: Page 22)
    fig, ax = plt.subplots(figsize=get_edp_figsize("full", "std"))

    # 2. Data: Forecast Example
    cats = ["2023", "2024", "2025 (f)"]
    vals = [45, 48, 52]
    # Mask: True for forecast (used for tinting per Page 8f)
    is_forecast = [False, False, True]

    # 3. Plot
    # Gap width 50% implies bar width ~0.66 (Reference: Page 8e)
    bars = ax.bar(cats, vals, width=0.66, color=SPG_FULL["Ocean"][7], label="Revenue")

    # 4. Style
    ax.set_title("Revenue Forecast")

    # Reference: Page 8a "Units: ... place unit at end of title"
    # (Or standardized top-of-axis placement)
    style.set_y_unit_label(ax, "($M)")

    # Apply specific bar styles (Labeling, Forecast Tints)
    style.style_bar_single(ax, bars, decimals=1, is_forecast_mask=is_forecast)

    # Add Footnotes (Reference: Page 25)
    style.add_footnotes(fig, notes=["(f) = forecast"])

    style.save_figure(fig, "edp_forecast_example.png")
    print("Generated: edp_forecast_example.png")
