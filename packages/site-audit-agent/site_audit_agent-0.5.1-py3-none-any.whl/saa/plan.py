"""Audit plan loading and parsing."""

from pathlib import Path
from typing import Optional

# Default audit plan (embedded)
DEFAULT_PLAN = """
# Default Website Audit Plan

## General Site Overview
- Infer site type (e.g., e-commerce, blog, portfolio) from structure/content.
- Detect tech stack (CMS, frameworks) via headers/source.
- Note overall performance (load time <3s ideal).

## SEO Checks
- Check HTTPS usage, meta tags (title/description), canonicals, URL structure.
- For own sites: Flag issues like mixed content, duplicate metas, broken links.
- For competitors: Note effective strategies worth adopting.

## Structured Data and Schema Checks
- Detect schema.org/JSON-LD (Organization, Product, FAQ, etc.).
- Validate implementation, flag errors or missing schemas.

## Open Graph and Social Sharing
- Verify OG metas (title, description, image, url).
- Check image dimensions (1200x630px recommended).

## Image Optimization
- Scan images for alt text, sizes, formats.
- Flag large images (>500KB), non-WebP/AVIF formats, missing alts.

## Performance
- Measure load times.
- Identify bottlenecks (large JS/CSS, third-party scripts).

## Accessibility (Own Sites)
- Check heading structure, ARIA usage, form labels.

## Security (Own Sites)
- Cert validity, mixed content, cookie flags.

## Report Format
- For own sites: Prioritized issues with severity (high/medium/low).
- For competitors: "What They Do Well" and "Ideas to Borrow" sections.
"""


def load_plan(plan_path: Optional[str] = None) -> str:
    """Load an audit plan from file or return default.

    Args:
        plan_path: Path to a markdown audit plan file

    Returns:
        The plan content as a string
    """
    if plan_path:
        path = Path(plan_path)
        if path.exists():
            return path.read_text()
        raise FileNotFoundError(f"Audit plan not found: {plan_path}")

    return DEFAULT_PLAN


def get_plan_sections(plan_content: str) -> list[str]:
    """Extract section headers from a plan.

    Args:
        plan_content: The markdown plan content

    Returns:
        List of section headers (## lines)
    """
    sections = []
    for line in plan_content.split("\n"):
        if line.startswith("## "):
            sections.append(line[3:].strip())
    return sections
