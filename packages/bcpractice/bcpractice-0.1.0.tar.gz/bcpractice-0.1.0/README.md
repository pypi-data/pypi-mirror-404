<div align="center">

# bcpractice

**AI-powered AP Calculus BC practice problem generator**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/bcpractice.svg)](https://pypi.org/project/bcpractice/)

Generate exam-quality practice sets in seconds. Select your topics, choose your length, get a professional PDF.

[Installation](#installation) • [Quick Start](#quick-start) • [Features](#features) • [Topics](#topic-coverage)

</div>

---

## Why bcpractice?

Preparing for the AP Calculus BC exam requires extensive practice. Creating quality problem sets manually is time-consuming. **bcpractice** solves this by leveraging AI to generate diverse, curriculum-aligned problems instantly.

- **Instant generation** — Full practice sets in under a minute
- **Exam-authentic** — Problems mirror actual AP free-response format
- **Complete curriculum** — All 10 units, 111 topics covered
- **Print-ready PDFs** — Professional LaTeX formatting with score tables and workspace

## Installation

```bash
pip install bcpractice
```

### Requirements

- **Python 3.9+**
- **LaTeX distribution** (for PDF compilation):

  | Platform | Command |
  |----------|---------|
  | macOS | `brew install --cask mactex` |
  | Ubuntu/Debian | `sudo apt install texlive-full` |
  | Windows | [MiKTeX](https://miktex.org/download) |

- **API Key** — OpenAI or Anthropic (bring your own)

## Quick Start

### 1. Configure your API key

```bash
bcpractice setup
```

Select your provider (OpenAI or Anthropic) and enter your API key. Configuration is stored locally in `~/.bcpractice/`.

### 2. Generate problems

```bash
bcpractice generate
```

Follow the interactive prompts to:
1. Select topics (by unit or individual topics)
2. Choose length (Quick / Medium / Full)
3. Receive your PDF

### 3. Start practicing

Your PDF includes:
- Cover page with name/date fields
- Organized sections by technique
- Point values for each problem
- Adequate workspace for solutions

## Features

| Feature | Description |
|---------|-------------|
| **Flexible Selection** | Choose entire units or cherry-pick specific topics |
| **Three Lengths** | Quick (5-8), Medium (12-15), or Full (20-25) problems |
| **Smart Sectioning** | Problems organized by technique (Riemann Sums, FTC, etc.) |
| **Graph Support** | Auto-generated TikZ graphs for visual problems |
| **Difficulty Mix** | ~30% basic, ~50% moderate, ~20% challenging |
| **Multi-part Problems** | Complex problems with labeled parts (a, b, c...) |

## Commands

| Command | Description |
|---------|-------------|
| `bcpractice setup` | Configure API provider and key |
| `bcpractice generate` | Generate a new practice set |
| `bcpractice topics` | List all available topics |
| `bcpractice reset` | Clear saved configuration |

### Options

```bash
bcpractice generate --output ./exams    # Custom output directory
bcpractice generate --length quick      # Skip length prompt
```

## Topic Coverage

Full AP Calculus BC curriculum based on the College Board Course and Exam Description.

| Unit | Name | Topics |
|:----:|------|:------:|
| 1 | Limits and Continuity | 16 |
| 2 | Differentiation: Definition and Fundamental Properties | 10 |
| 3 | Differentiation: Composite, Implicit, and Inverse Functions | 6 |
| 4 | Contextual Applications of Differentiation | 7 |
| 5 | Analytical Applications of Differentiation | 12 |
| 6 | Integration and Accumulation of Change | 14 |
| 7 | Differential Equations | 9 |
| 8 | Applications of Integration | 13 |
| 9 | Parametric, Polar, and Vector Functions | 9 |
| 10 | Infinite Sequences and Series | 15 |

> Topics marked **[BC]** are exclusive to Calculus BC and not covered in AB.

## Configuration

### Environment Variables

Skip `bcpractice setup` by setting environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Config Location

Configuration is stored at `~/.bcpractice/config.json` with restricted permissions (600).

## Example Output

Generated PDFs feature:

```
┌─────────────────────────────────────────┐
│           BC Calculus                   │
│        Practice Problems                │
│     Unit 6: Integration                 │
├─────────────────────────────────────────┤
│  Name: _____________  Date: _________   │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Instructions                    │    │
│  │ • 13 problems (52 points)       │    │
│  │ • No calculator unless marked   │    │
│  │ • Show all work                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Section A: Riemann Sums     12 pts     │
│  Section B: FTC              20 pts     │
│  Section C: U-Substitution   20 pts     │
│  ───────────────────────────────────    │
│  TOTAL                       52 pts     │
└─────────────────────────────────────────┘
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, open an issue first to discuss what you'd like to change.

## License

[MIT](LICENSE) — Use it freely.

## Acknowledgments

- Curriculum structure: [College Board AP Calculus BC](https://apcentral.collegeboard.org/courses/ap-calculus-bc)
- Topic organization: [FlippedMath](https://calculus.flippedmath.com)

---

<div align="center">

**[Report Bug](https://github.com/aaravjaichand/bc-calc-practice/issues)** • **[Request Feature](https://github.com/aaravjaichand/bc-calc-practice/issues)**

Made for students, by a student.

</div>
