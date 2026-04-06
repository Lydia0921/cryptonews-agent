# PPTX Skill Documentation

## Overview
This skill handles all PowerPoint presentations (.pptx files), including creation, editing, reading, and manipulation tasks.

## Key Commands

**Text Extraction:**
```bash
python -m markitdown presentation.pptx
```

**Visual Preview:**
```bash
python scripts/thumbnail.py presentation.pptx
```

**Create from Scratch:**
Consult pptxgenjs.md documentation for detailed guidance.

## Design Principles

The documentation emphasizes avoiding generic presentations. Key recommendations include:

- **Color Selection**: "Pick a bold, content-informed color palette" rather than defaulting to blue. The primary color should dominate 60-70% of visual weight with supporting and accent colors.

- **Visual Elements**: "Every slide needs a visual element — image, chart, icon, or shape. Text-only slides are forgettable."

- **Layout Variety**: Use two-column layouts, icon-text rows, grids, and half-bleed images rather than repeating the same format.

- **Typography**: Select font pairings with personality; titles should be 36-44pt, body text 14-16pt.

## Quality Assurance Workflow

1. Generate slides and convert to images
2. Inspect visually for overlaps, alignment issues, contrast problems
3. Fix identified issues
4. Re-verify affected slides
5. Repeat until no new issues appear

The documentation notes: "Use subagents" for visual inspection to catch errors that creators might miss.
