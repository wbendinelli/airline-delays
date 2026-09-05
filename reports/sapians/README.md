# SAPIANS Typst Package (`@local/sapians:0.1.0`)

Official document & presentation design system for SAPIANS, built with modern Typst and calibrated against **Google DeepMind**, **Anthropic Research**, and **Urban Institute** publication standards.

## Features

- **16:9 Presentation Engine**: 10 standardized slide families (`slide-cover`, `slide-problem`, `slide-definition`, `slide-equation`, `slide-three-column`, `slide-evidence`, `slide-limitation`, `slide-contrast`, `slide-takeaway`, `slide-index`).
- **Academic Paper Template (`sapians-article`)**: Two-column IEEE/ACM-style format with abstract box, author metadata, and automated bibliography.
- **Executive Report / Technical Memo (`sapians-report`)**: Single-column clean document format with versioning and date headers.
- **Micro-Typography**: Calibrated font scales (Inter + JetBrains Mono), 0.25pt hairline rules, and terracotta intervention tags.
- **WCAG AA Accessible**: Validated color contrast ratios across all text and UI elements.

## Quick Start

```typst
#import "@local/sapians:0.1.0": *

#show: sapians-slides.with(
  title: "SAPIANS Machine Intelligence",
  author: "Research Team",
)

#slide-cover(
  title: "SAPIANS",
  subtitle: "Foundations of Neural Systems",
)
```

## Installation

Run the automated installer script:

```bash
bash scripts/install_theme.sh
```
