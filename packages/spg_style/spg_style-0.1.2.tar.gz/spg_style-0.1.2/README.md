# S&P Global EDP Chart Style for Python

**Disclaimer:** This is **NOT** an official package provided by S&P Global. It is a community-driven project created by analysts to style visualizations in Python. Please reach out to support.energy@spglobal.com for official support, and more information on the use of S&P Global data.

A Python implementation of the **S&P Global Editorial, Design & Publishing (EDP)** standards for data visualization using Matplotlib. This package ensures your charts adhere to strict brand guidelines regarding colors, typography, layout, and formatting.

## 🚀 Key Features

- **Strict Brand Colors**: Full access to the S&P Global color palette (Levels 1-12) for all brand colors.
- **Theming**: Native support for **Standard Light** and **Standard Dark** modes.
- **Auto-Styling**: Specialized methods to style bar charts, line charts, and dual-axis charts according to EDP rules.
- **Intelligent Layout**:
    - **EDP Figure Sizing**: `get_edp_figsize()` returns exact dimensions for digital reports (Word/InDesign) or PowerPoint (16x9).
    - **Header/Footer Management**: Automatic footnote generation including dynamic "As of" dates, source attribution, and copyright.
    - **Legend Positioning**: Automatically aligns legends to the top with smart column calculation.
- **Advanced Formatting**:
    - **Forecast Tints**: Automatically apply lighter tints for forecast data.
    - **Monochromatic Palettes**: Compliant palettes for 2 to 5 classes.
    - **Date Alignment**: Standardized 3-letter month abbreviations (Jan, Feb, Sep, etc.) without periods.

## 📦 Installation

This project is managed by [Poetry](https://python-poetry.org/).

```bash
git clone https://github.com/kovzhu/spg_style.git
cd spg_style
poetry install
```

## 🛠 Usage

### 1. Basic Setup in Jupyter Notebook
To see changes reflected immediately when editing `spg_style.py`, use `%autoreload`:

```python
%load_ext autoreload
%autoreload 2

import spg_style as spg
import matplotlib.pyplot as plt

# Initialize the EDP style (sets global rcParams)
style = spg.SpglobalStyle(theme='light')
```

### 2. Creating an EDP Compliant Chart

```python
import pandas as pd

# 1. Get the correct dimensions for a half-page report graphic
figsize = spg.get_edp_figsize(width="full", height="1/2", target="report")
fig, ax = plt.subplots(figsize=figsize)

# 2. Plot your data
data = pd.Series([10, 15, 7, 12], index=['Q1', 'Q2', 'Q3', 'Q4 (F)'])
bars = ax.bar(data.index, data.values)

# 3. Apply EDP styling rules
# - tints Q4 if marked as forecast
# - adds value labels
# - sets standard bar widths
style.style_bar_single(ax, bars, is_forecast_mask=[False, False, False, True])

# 4. Final Polish
style.set_y_unit_label(ax, "USD Millions")
style.add_footnotes(fig, source="S&P Global Commodity Insights")

plt.show()
```

## 🎨 Color Palette
The package provides the full `SPG_FULL` dictionary containing hex codes transcribed from the EDP guidelines.

```python
from spg_style import SPG_FULL

# Access Maroon Level 7
primary_color = SPG_FULL["Maroon"][7]

# Access Sentiment colors
from spg_style import SENTIMENT
positive_color = SENTIMENT["positive"]
```

## 🏗 Project Structure
- `spg_style/spg_style.py`: The core engine containing the `SpglobalStyle` class and color definitions.
- `notebook/notebook.ipynb`: Examples and scratchpad for testing new chart styles.
- `pyproject.toml`: Dependency management and project metadata.

## 📄 Reference
This implementation is based on the **S&P Global EDP Visual Style Guide (Jan 2026)**.
