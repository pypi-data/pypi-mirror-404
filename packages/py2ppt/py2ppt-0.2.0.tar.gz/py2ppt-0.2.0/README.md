# py2ppt

AI-Native PowerPoint Library for Python

## Overview

py2ppt is a Python library for creating and manipulating PowerPoint presentations, designed from the ground up for:

- **AI/Agent-first interaction** - Tool-calling interface with granular functions optimized for LLM agents
- **Template-centric workflow** - Corporate templates and style guides as first-class citizens
- **Semantic abstraction** - Work with intent, not XML coordinates
- **Zero legacy dependencies** - Pure Python Open XML handling

## Installation

```bash
pip install py2ppt
```

Or install from source:

```bash
git clone https://github.com/py2ppt/py2ppt.git
cd py2ppt
pip install -e .
```

## Quick Start

```python
import py2ppt as ppt

# Create a new presentation
pres = ppt.create_presentation()

# Add a title slide
ppt.add_slide(pres, layout="Title Slide")
ppt.set_title(pres, 1, "Hello World")
ppt.set_subtitle(pres, 1, "My first py2ppt presentation")

# Add a content slide
ppt.add_slide(pres, layout="Title and Content")
ppt.set_title(pres, 2, "Key Points")
ppt.set_body(pres, 2, [
    "Simple, clean API",
    "Designed for AI agents",
    "Works with any template"
])

# Save
ppt.save_presentation(pres, "output.pptx")
```

## AI Agent Workflow

py2ppt is designed for AI agents to create presentations autonomously:

```python
import py2ppt as ppt

# Step 1: Agent opens template and inspects capabilities
pres = ppt.create_presentation(template="corporate.pptx")
layouts = ppt.list_layouts(pres)
colors = ppt.get_theme_colors(pres)

# Agent now knows:
# - Available layouts and their placeholders
# - Theme colors to use for consistency

# Step 2: Agent creates content
ppt.add_slide(pres, layout="Title and Content")
ppt.set_title(pres, 1, "Q4 Business Review")
ppt.set_body(pres, 1, [
    "Revenue: $4.2M (+20% YoY)",
    "New customers: 1,247",
    "NPS Score: 72"
])

# Step 3: Agent saves result
ppt.save_presentation(pres, "q4_review.pptx")
```

## API Reference

### Presentation Tools

```python
# Create presentations
pres = ppt.create_presentation()                    # Blank presentation
pres = ppt.create_presentation(template="corp.pptx")  # From template

# Open and save
pres = ppt.open_presentation("existing.pptx")
ppt.save_presentation(pres, "output.pptx")
```

### Slide Tools

```python
# Add slides
slide_num = ppt.add_slide(pres, layout="Title and Content")
slide_num = ppt.add_slide(pres, layout="Title Slide", position=1)

# Manage slides
ppt.delete_slide(pres, slide_number=3)
ppt.duplicate_slide(pres, slide_number=2)
ppt.reorder_slides(pres, order=[2, 1, 3])
```

### Content Tools

```python
# Set text content
ppt.set_title(pres, 1, "Slide Title")
ppt.set_subtitle(pres, 1, "Subtitle text")
ppt.set_body(pres, 1, ["Bullet 1", "Bullet 2", "Bullet 3"])

# Nested bullets with levels
ppt.set_body(pres, 2, [
    "Main point",
    "Sub-point 1",
    "Sub-point 2",
    "Another main point"
], levels=[0, 1, 1, 0])

# Add individual bullets
ppt.add_bullet(pres, 1, "Additional point")
ppt.add_bullet(pres, 1, "Sub-point", level=1)

# Tables
ppt.add_table(pres, 1, data=[
    ["Region", "Q3", "Q4"],
    ["North", 100, 120],
    ["South", 80, 95],
])

# Images
ppt.add_image(pres, 1, "chart.png", placeholder="content")
```

### Inspection Tools

```python
# Discover template capabilities
layouts = ppt.list_layouts(pres)
# [{"name": "Title Slide", "index": 0, "placeholders": ["title", "subtitle"]}, ...]

# Get slide content
info = ppt.describe_slide(pres, slide_number=1)
# {"slide_number": 1, "placeholders": {"title": "...", "body": [...]}, ...}

# Theme information
colors = ppt.get_theme_colors(pres)
# {"accent1": "#4472C4", "accent2": "#ED7D31", ...}

fonts = ppt.get_theme_fonts(pres)
# {"heading": "Calibri Light", "body": "Calibri"}
```

### Styling Tools

```python
ppt.set_text_style(pres, 1, "title",
    font="Arial Black",
    size="32pt",
    color="#0066CC",
    bold=True
)
```

## Comparison with python-pptx

### python-pptx (22 lines)
```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RgbColor

prs = Presentation('template.pptx')
slide_layout = prs.slide_layouts[1]  # Magic number!
slide = prs.slides.add_slide(slide_layout)

title = slide.shapes.title
title.text = "Q4 Review"

body = slide.placeholders[1]  # Another magic number!
tf = body.text_frame
tf.clear()
p = tf.paragraphs[0]
p.text = "Revenue increased 20%"
p.font.size = Pt(18)
p.font.color.rgb = RgbColor(0x00, 0x66, 0xCC)

p2 = tf.add_paragraph()
p2.text = "New markets opened"
p2.font.size = Pt(18)

prs.save('output.pptx')
```

### py2ppt (6 lines)
```python
import py2ppt as ppt

pres = ppt.create_presentation(template="template.pptx")
ppt.add_slide(pres, layout="Title and Content")
ppt.set_title(pres, 1, "Q4 Review")
ppt.set_body(pres, 1, ["Revenue increased 20%", "New markets opened"], color="#0066CC")
ppt.save_presentation(pres, "output.pptx")
```

## Design Tokens

Define and enforce brand guidelines:

```python
from py2ppt.template.tokens import create_tokens, save_tokens

tokens = create_tokens({
    "colors": {
        "brand-primary": "#0066CC",
        "brand-secondary": "#FF6600",
        "text-dark": "#333333"
    },
    "fonts": {
        "heading": {"family": "Arial Black", "size": "32pt"},
        "body": {"family": "Arial", "size": "14pt"}
    }
})

save_tokens(tokens, "brand_tokens.json")
```

## Style Guide Validation

Validate presentations against corporate guidelines:

```python
from py2ppt.validation import create_style_guide, validate

rules = create_style_guide({
    "max_bullet_points": 6,
    "max_words_per_bullet": 12,
    "max_slides": 30,
    "forbidden_fonts": ["Comic Sans MS", "Papyrus"],
    "min_font_size": 12
})

issues = validate(pres, rules)
for issue in issues:
    print(f"Slide {issue.slide}: {issue.message}")
```

## Features

- Create presentations from scratch or templates
- Semantic layout names (no magic idx numbers)
- Fuzzy layout matching ("title" matches "Title Slide")
- Tables with automatic sizing
- Image insertion with placeholder support
- Theme color and font extraction
- Design token system for brand consistency
- Style guide validation
- Full type hints for IDE support
- Structured errors for AI self-correction

## Requirements

- Python 3.10+
- lxml

## License

MIT License - see LICENSE file for details.
