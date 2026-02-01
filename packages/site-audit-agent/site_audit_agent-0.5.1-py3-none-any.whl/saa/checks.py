"""Audit checks for analyzing crawled pages."""

from typing import Callable
from saa.models import PageData, Finding, Severity, CheckResult


# Check registry
CHECK_REGISTRY: dict[str, Callable[[PageData], list[Finding]]] = {}


def register_check(name: str):
    """Decorator to register a check function."""
    def decorator(func: Callable[[PageData], list[Finding]]):
        CHECK_REGISTRY[name] = func
        return func
    return decorator


def run_checks(pages: list[PageData], check_names: list[str] | None = None) -> list[Finding]:
    """Run specified checks on all pages, return all findings."""
    if check_names is None:
        check_names = list(CHECK_REGISTRY.keys())

    all_findings = []
    for page in pages:
        if page.error:
            # Skip pages that failed to load
            continue
        for name in check_names:
            if name in CHECK_REGISTRY:
                findings = CHECK_REGISTRY[name](page)
                all_findings.extend(findings)

    return all_findings


def get_available_checks() -> list[str]:
    """Return list of available check names."""
    return list(CHECK_REGISTRY.keys())


# ============== Built-in Checks ==============


@register_check("meta_tags")
def check_meta_tags(page: PageData) -> list[Finding]:
    """Check for essential meta tags."""
    findings = []

    # Title check
    if not page.title:
        findings.append(Finding(
            check_name="meta_tags",
            severity=Severity.HIGH,
            message="Missing page title",
            url=page.url,
            suggestion="Add a descriptive <title> tag (50-60 characters ideal)",
        ))
    elif len(page.title) > 60:
        findings.append(Finding(
            check_name="meta_tags",
            severity=Severity.LOW,
            message=f"Title too long ({len(page.title)} chars)",
            url=page.url,
            evidence=f'"{page.title[:70]}..."',
            suggestion="Keep title under 60 characters for optimal display in search results",
        ))
    elif len(page.title) < 20:
        findings.append(Finding(
            check_name="meta_tags",
            severity=Severity.LOW,
            message=f"Title may be too short ({len(page.title)} chars)",
            url=page.url,
            evidence=f'"{page.title}"',
            suggestion="Consider a more descriptive title (30-60 characters)",
        ))

    # Description check
    if not page.description:
        findings.append(Finding(
            check_name="meta_tags",
            severity=Severity.MEDIUM,
            message="Missing meta description",
            url=page.url,
            suggestion="Add a meta description (150-160 characters) for better SEO",
        ))
    elif len(page.description) > 160:
        findings.append(Finding(
            check_name="meta_tags",
            severity=Severity.LOW,
            message=f"Meta description too long ({len(page.description)} chars)",
            url=page.url,
            evidence=f'"{page.description[:80]}..."',
            suggestion="Keep meta description under 160 characters",
        ))

    # H1 check
    if not page.h1_tags:
        findings.append(Finding(
            check_name="meta_tags",
            severity=Severity.MEDIUM,
            message="Missing H1 heading",
            url=page.url,
            suggestion="Add a single H1 heading that describes the page content",
        ))
    elif len(page.h1_tags) > 1:
        findings.append(Finding(
            check_name="meta_tags",
            severity=Severity.LOW,
            message=f"Multiple H1 headings ({len(page.h1_tags)} found)",
            url=page.url,
            evidence=", ".join(f'"{h}"' for h in page.h1_tags[:3]),
            suggestion="Use only one H1 per page for better SEO structure",
        ))

    # Canonical check
    if not page.canonical:
        findings.append(Finding(
            check_name="meta_tags",
            severity=Severity.LOW,
            message="Missing canonical URL",
            url=page.url,
            suggestion="Add a canonical link to prevent duplicate content issues",
        ))

    return findings


@register_check("open_graph")
def check_open_graph(page: PageData) -> list[Finding]:
    """Check Open Graph metadata for social sharing."""
    findings = []

    if not page.og_data:
        findings.append(Finding(
            check_name="open_graph",
            severity=Severity.LOW,
            message="Missing Open Graph metadata",
            url=page.url,
            suggestion="Add og:title, og:description, og:image for better social sharing",
        ))
        return findings

    og = page.og_data

    if not og.title:
        findings.append(Finding(
            check_name="open_graph",
            severity=Severity.LOW,
            message="Missing og:title",
            url=page.url,
            suggestion="Add og:title for social sharing previews",
        ))

    if not og.description:
        findings.append(Finding(
            check_name="open_graph",
            severity=Severity.LOW,
            message="Missing og:description",
            url=page.url,
            suggestion="Add og:description for social sharing previews",
        ))

    if not og.image:
        findings.append(Finding(
            check_name="open_graph",
            severity=Severity.LOW,
            message="Missing og:image",
            url=page.url,
            suggestion="Add og:image (1200x630px recommended) for visual social previews",
        ))

    return findings


@register_check("image_optimization")
def check_image_optimization(page: PageData) -> list[Finding]:
    """Check image optimization and alt text."""
    findings = []

    images_without_alt = []
    legacy_formats = []

    for img in page.images:
        # Check alt text
        if not img.alt:
            images_without_alt.append(img.src)

        # Check format (prefer webp/avif)
        if img.format in ["jpg", "jpeg", "png", "gif"]:
            legacy_formats.append(img.src)

    # Report missing alt text
    if images_without_alt:
        count = len(images_without_alt)
        findings.append(Finding(
            check_name="image_optimization",
            severity=Severity.MEDIUM if count > 3 else Severity.LOW,
            message=f"{count} image(s) missing alt text",
            url=page.url,
            evidence="\n".join(images_without_alt[:5]) + ("..." if count > 5 else ""),
            suggestion="Add descriptive alt text for accessibility and SEO",
        ))

    # Report legacy formats
    if legacy_formats:
        count = len(legacy_formats)
        findings.append(Finding(
            check_name="image_optimization",
            severity=Severity.LOW,
            message=f"{count} image(s) using legacy formats (JPG/PNG/GIF)",
            url=page.url,
            evidence="\n".join(legacy_formats[:3]) + ("..." if count > 3 else ""),
            suggestion="Convert to WebP or AVIF for 25-50% smaller file sizes",
        ))

    return findings


@register_check("https_security")
def check_https_security(page: PageData) -> list[Finding]:
    """Check HTTPS usage."""
    findings = []

    if not page.is_https:
        findings.append(Finding(
            check_name="https_security",
            severity=Severity.HIGH,
            message="Page not served over HTTPS",
            url=page.url,
            suggestion="Enable HTTPS for security and SEO benefits",
        ))

    # Check for mixed content (http:// links/images on https page)
    if page.is_https:
        http_resources = []
        for img in page.images:
            if img.src.startswith("http://"):
                http_resources.append(f"Image: {img.src}")
        for link in page.links:
            if link.href.startswith("http://") and link.is_internal:
                http_resources.append(f"Link: {link.href}")

        if http_resources:
            findings.append(Finding(
                check_name="https_security",
                severity=Severity.MEDIUM,
                message=f"Mixed content: {len(http_resources)} HTTP resource(s) on HTTPS page",
                url=page.url,
                evidence="\n".join(http_resources[:5]),
                suggestion="Update all internal resources to use HTTPS",
            ))

    return findings


@register_check("performance")
def check_performance(page: PageData) -> list[Finding]:
    """Check basic performance metrics."""
    findings = []

    if page.load_time_ms is not None:
        if page.load_time_ms > 5000:
            findings.append(Finding(
                check_name="performance",
                severity=Severity.HIGH,
                message=f"Slow page load: {page.load_time_ms:.0f}ms",
                url=page.url,
                evidence=f"Load time: {page.load_time_ms/1000:.1f}s (target: <3s)",
                suggestion="Investigate slow resources, enable compression, optimize images",
            ))
        elif page.load_time_ms > 3000:
            findings.append(Finding(
                check_name="performance",
                severity=Severity.MEDIUM,
                message=f"Page load could be faster: {page.load_time_ms:.0f}ms",
                url=page.url,
                evidence=f"Load time: {page.load_time_ms/1000:.1f}s (target: <3s)",
                suggestion="Consider optimizing for faster initial load",
            ))

    # Check total images count (too many = performance issue)
    if len(page.images) > 30:
        findings.append(Finding(
            check_name="performance",
            severity=Severity.LOW,
            message=f"High image count: {len(page.images)} images",
            url=page.url,
            suggestion="Consider lazy loading or reducing image count",
        ))

    return findings


@register_check("schema_data")
def check_schema_data(page: PageData) -> list[Finding]:
    """Check for structured data / JSON-LD."""
    findings = []

    if not page.schema_types:
        findings.append(Finding(
            check_name="schema_data",
            severity=Severity.LOW,
            message="No structured data (JSON-LD) found",
            url=page.url,
            suggestion="Add schema.org markup for rich search results (Organization, Product, FAQ, etc.)",
        ))
    else:
        # Info-level finding to report what was found
        findings.append(Finding(
            check_name="schema_data",
            severity=Severity.INFO,
            message=f"Found structured data: {', '.join(page.schema_types)}",
            url=page.url,
        ))

    return findings


# Default checks to run in each mode
DEFAULT_CHECKS_OWN = [
    "meta_tags",
    "open_graph",
    "image_optimization",
    "https_security",
    "performance",
    "schema_data",
]

DEFAULT_CHECKS_COMPETITOR = [
    "meta_tags",
    "open_graph",
    "image_optimization",
    "schema_data",
]
