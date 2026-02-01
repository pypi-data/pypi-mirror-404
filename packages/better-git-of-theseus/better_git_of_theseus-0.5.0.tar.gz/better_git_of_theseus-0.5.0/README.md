<div align="center">

# Better Git of Theseus

[![pypi badge](https://img.shields.io/pypi/v/better-git-of-theseus.svg?style=flat)](https://pypi.python.org/pypi/better-git-of-theseus)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/better-git-of-theseus)](https://pypi.org/project/better-git-of-theseus/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/better-git-of-theseus)](https://pypi.org/project/better-git-of-theseus/)
[![GitHub License](https://img.shields.io/github/license/onewesong/better-git-of-theseus)](https://github.com/onewesong/better-git-of-theseus/blob/master/LICENSE)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/onewesong/better-git-of-theseus)

[中文版](README_zh.md)

</div>

**Better Git of Theseus** is a modern refactor of the original [git-of-theseus](https://github.com/erikbern/git-of-theseus). It provides a fully interactive Web Dashboard powered by **Streamlit** and **Plotly**, making it easier than ever to visualize how your code evolves over time.

![Git of Theseus Cohorts](pics/plot-cohorts.png)
![Git of Theseus Authors](pics/plot-authors.png)

## Key Enhancements

-   🚀 **One-Click Visualization**: New `better-git-of-theseus` command automatically scans your project and launches a Web UI.
-   📊 **Interactive Charts**: Replaced static Matplotlib plots with Plotly. Support for zooming, panning, and detailed data hovers.
-   🧠 **In-Memory Processing**: Data flows directly in memory. No more mandatory intermediate `.json` files cluttering your repo.
-   ⚡ **Smart Caching**: Leverages Streamlit's caching to make repeat analysis of large repos nearly instantaneous.
-   🎨 **Modern UI**: Adjust parameters (Cohort format, ignore rules, normalization, etc.) in real-time via the sidebar.

## Installation

Install via pip:

```bash
pip install better-git-of-theseus
```

## Quick Start

Run the following in any Git repository:

```bash
better-git-of-theseus
```

It will automatically open your browser to the interactive dashboard.

## Feature Highlights

### Cohort Formatting

Customize how commits are grouped by year, month, or week (based on Python strftime):
-   `%Y`: Group by **Year** (Default)
-   `%Y-%m`: Group by **Month**
-   `%Y-W%W`: Group by **Week**

### Real-time Parameters

Adjust parameters like "Max Series", "Normalization", and "Exponential Fit" directly in the Web UI without re-running any commands.

## FAQ

-   **Duplicate Authors?** Configure a [.mailmap](https://git-scm.com/docs/gitmailmap) file in your repo root to merge identities.
-   **Performance?** First-time analysis of very large repos (like the Linux Kernel) may take time, but subsequent views are extremely fast due to caching.

## Credits

Special thanks to [Erik Bernhardsson](https://github.com/erikbern) for creating the original `git-of-theseus`.

## License

MIT
