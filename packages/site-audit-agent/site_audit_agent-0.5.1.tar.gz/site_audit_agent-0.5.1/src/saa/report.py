"""Report generation with LLM enhancement."""

from datetime import datetime
from typing import Optional

from saa.models import PageData, Finding, Severity
from saa.llm import LLMClient


def generate_report(
    start_url: str,
    pages: list[PageData],
    findings: list[Finding],
    mode: str,
    llm_client: Optional[LLMClient] = None,
    verbose: bool = False,
    plan_content: Optional[str] = None,
) -> str:
    """Generate audit report, optionally enhanced with LLM analysis.

    Args:
        start_url: The starting URL for the audit
        pages: List of crawled pages
        findings: List of findings from checks
        mode: "own" or "competitor"
        llm_client: Optional LLM client for enhanced analysis
        verbose: Whether to print progress
        plan_content: Optional audit plan content (markdown) to guide analysis

    Returns:
        Formatted markdown report
    """
    # Build the basic report structure
    report_data = _build_report_data(start_url, pages, findings, mode)

    if llm_client:
        if verbose:
            print("Generating LLM-enhanced analysis...")
        report_data = _enhance_with_llm(report_data, llm_client, mode, verbose, plan_content)

    return _format_report(report_data, mode)


def _build_report_data(
    start_url: str,
    pages: list[PageData],
    findings: list[Finding],
    mode: str,
) -> dict:
    """Build structured report data."""
    successful = [p for p in pages if not p.error]
    failed = [p for p in pages if p.error]

    # Count findings by severity
    severity_counts = {}
    for sev in Severity:
        count = sum(1 for f in findings if f.severity == sev)
        if count > 0:
            severity_counts[sev.value] = count

    # Group findings by check
    findings_by_check = {}
    for f in findings:
        if f.check_name not in findings_by_check:
            findings_by_check[f.check_name] = []
        findings_by_check[f.check_name].append({
            "severity": f.severity.value,
            "message": f.message,
            "url": f.url,
            "evidence": f.evidence,
            "suggestion": f.suggestion,
        })

    # Page summaries
    page_summaries = []
    for p in successful:
        page_summaries.append({
            "url": p.url,
            "title": p.title,
            "description": p.description,
            "load_time_ms": p.load_time_ms,
            "links_count": len(p.links),
            "images_count": len(p.images),
            "has_schema": bool(p.schema_types),
            "schema_types": p.schema_types,
            "depth": p.depth,
        })

    return {
        "start_url": start_url,
        "mode": mode,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "pages_crawled": len(pages),
            "pages_successful": len(successful),
            "pages_failed": len(failed),
            "total_links": sum(len(p.links) for p in successful),
            "total_images": sum(len(p.images) for p in successful),
            "avg_load_time_ms": sum(p.load_time_ms or 0 for p in successful) / len(successful) if successful else 0,
        },
        "severity_counts": severity_counts,
        "findings_by_check": findings_by_check,
        "findings": [
            {
                "check_name": f.check_name,
                "severity": f.severity.value,
                "message": f.message,
                "url": f.url,
                "evidence": f.evidence,
                "suggestion": f.suggestion,
            }
            for f in findings
        ],
        "pages": page_summaries,
        "failed_pages": [{"url": p.url, "error": p.error} for p in failed],
        # LLM-enhanced fields (populated later if LLM available)
        "executive_summary": None,
        "top_priorities": None,
        "competitor_insights": None,
    }


def _enhance_with_llm(report_data: dict, llm_client: LLMClient, mode: str, verbose: bool, plan_content: Optional[str] = None) -> dict:
    """Enhance report with LLM-generated analysis."""

    # Prepare FULL context for LLM - all pages, all findings with URLs

    # All pages with details
    pages_summary = []
    for p in report_data["pages"]:
        pages_summary.append(
            f"- {p['url']}\n"
            f"  Title: {p['title'] or '(missing)'} ({len(p['title']) if p['title'] else 0} chars)\n"
            f"  Description: {(p['description'][:80] + '...') if p['description'] and len(p['description']) > 80 else p['description'] or '(missing)'} ({len(p['description']) if p['description'] else 0} chars)\n"
            f"  Load time: {p['load_time_ms']:.0f}ms | Images: {p['images_count']} | Links: {p['links_count']}\n"
            f"  Schema: {', '.join(p['schema_types']) if p['schema_types'] else 'none'}"
        )

    # All findings grouped by URL
    findings_by_url = {}
    for f in report_data["findings"]:
        url = f["url"]
        if url not in findings_by_url:
            findings_by_url[url] = []
        findings_by_url[url].append(f)

    findings_summary = []
    for url, url_findings in findings_by_url.items():
        findings_summary.append(f"\n{url}:")
        for f in url_findings:
            evidence_short = f["evidence"][:100] if f["evidence"] else ""
            findings_summary.append(f"  - [{f['severity'].upper()}] {f['check_name']}: {f['message']}")
            if evidence_short:
                findings_summary.append(f"    Evidence: {evidence_short}")

    context = f"""
Site: {report_data['start_url']}
Mode: {mode}
Pages crawled: {report_data['summary']['pages_crawled']}
Total images: {report_data['summary']['total_images']}
Total links: {report_data['summary']['total_links']}
Average load time: {report_data['summary']['avg_load_time_ms']:.0f}ms

=== ALL PAGES ANALYZED ===
{chr(10).join(pages_summary)}

=== ALL FINDINGS BY URL ===
{chr(10).join(findings_summary)}
"""

    # If a custom plan is provided, use it to structure the analysis
    if plan_content:
        prompt = f"""You are conducting a website audit following this audit plan:

--- AUDIT PLAN ---
{plan_content}
--- END PLAN ---

Here is the COMPLETE data collected from crawling the site:

{context}

Based on the audit plan and the data above, generate a comprehensive audit report.

IMPORTANT INSTRUCTIONS:
- Follow the structure and sections defined in the audit plan
- For mode "{mode}": {"Focus on issues, fixes, and compliance. List SPECIFIC URLs that need attention." if mode == "own" else "Focus on what they do well and ideas to borrow"}
- Be SPECIFIC: Always reference exact URLs, not "multiple pages" or "some pages"
- For each issue, list the exact pages affected
- Group recommendations by priority (High/Medium/Low impact)
- Include specific evidence from the crawl data

Generate the full audit report now."""

    elif mode == "own":
        prompt = f"""Analyze this website audit for the site owner. Be direct and actionable.

{context}

Provide:
1. EXECUTIVE SUMMARY (2-3 sentences): Overall site health and most critical issue
2. TOP 3 PRIORITIES: The most impactful fixes, ranked by importance. For each:
   - What to fix
   - Why it matters
   - How to fix it (specific action)

Be concise. Focus on actionable improvements. No fluff."""

    else:  # competitor mode
        prompt = f"""Analyze this competitor website audit. Focus on what they're doing well that we can learn from.

{context}

Provide:
1. EXECUTIVE SUMMARY (2-3 sentences): Overall impression and standout qualities
2. COMPETITOR STRENGTHS: 3-5 things they do well that we could adopt
3. IDEAS TO BORROW: Specific tactics or approaches worth considering

Be concise. Focus on learnings and inspiration, not criticism."""

    try:
        system = "You are a senior web developer and SEO expert. Provide clear, actionable analysis formatted in markdown."
        analysis = llm_client.complete(prompt, system)

        # Parse the analysis into sections
        report_data["llm_analysis"] = analysis

        if verbose:
            print("LLM analysis complete.")

    except Exception as e:
        if verbose:
            print(f"LLM analysis failed: {e}")
        report_data["llm_analysis"] = None

    return report_data


def _format_report(report_data: dict, mode: str) -> str:
    """Format report data as markdown."""
    lines = []

    # Header
    lines.append(f"# Site Audit Report: {report_data['start_url']}")
    lines.append("")
    lines.append(f"**Mode:** {mode.title()}")
    lines.append(f"**Generated:** {report_data['generated_at']}")
    lines.append("")

    # LLM Analysis (if available) - put at top for visibility
    if report_data.get("llm_analysis"):
        lines.append("---")
        lines.append("")
        lines.append("## Analysis")
        lines.append("")
        lines.append(report_data["llm_analysis"])
        lines.append("")

    # Crawl Summary
    lines.append("---")
    lines.append("")
    lines.append("## Crawl Summary")
    lines.append("")
    s = report_data["summary"]
    lines.append(f"- **Pages crawled:** {s['pages_crawled']} ({s['pages_successful']} successful, {s['pages_failed']} failed)")
    lines.append(f"- **Total links:** {s['total_links']}")
    lines.append(f"- **Total images:** {s['total_images']}")
    lines.append(f"- **Average load time:** {s['avg_load_time_ms']:.0f}ms")
    lines.append("")

    # Pages list
    lines.append("### Pages Analyzed")
    lines.append("")
    for p in report_data["pages"]:
        indent = "  " * p["depth"]
        title = (p["title"][:50] + "...") if p["title"] and len(p["title"]) > 50 else (p["title"] or "(no title)")
        schema_badge = f" [Schema: {', '.join(p['schema_types'])}]" if p["schema_types"] else ""
        lines.append(f"{indent}- [{title}]({p['url']}){schema_badge}")
    lines.append("")

    if report_data["failed_pages"]:
        lines.append("### Failed Pages")
        lines.append("")
        for p in report_data["failed_pages"]:
            lines.append(f"- {p['url']}: {p['error']}")
        lines.append("")

    # Findings Summary
    if report_data["severity_counts"]:
        lines.append("---")
        lines.append("")
        lines.append("## Findings Summary")
        lines.append("")
        for sev in ["critical", "high", "medium", "low", "info"]:
            if sev in report_data["severity_counts"]:
                lines.append(f"- **{sev.upper()}:** {report_data['severity_counts'][sev]}")
        lines.append("")

    # Detailed Findings
    if report_data["findings"]:
        lines.append("---")
        lines.append("")
        lines.append("## Detailed Findings")
        lines.append("")

        # Group by severity
        for sev in ["critical", "high", "medium", "low", "info"]:
            sev_findings = [f for f in report_data["findings"] if f["severity"] == sev]
            if not sev_findings:
                continue

            lines.append(f"### {sev.upper()}")
            lines.append("")

            # Group by URL within severity
            urls_seen = []
            for f in sev_findings:
                if f["url"] not in urls_seen:
                    urls_seen.append(f["url"])

            for url in urls_seen:
                url_findings = [f for f in sev_findings if f["url"] == url]
                if len(report_data["pages"]) > 1:
                    lines.append(f"**{url}**")
                    lines.append("")
                for f in url_findings:
                    lines.append(f"- **[{f['check_name']}]** {f['message']}")
                    if f["evidence"]:
                        evidence_preview = f["evidence"].split("\n")[0][:100]
                        lines.append(f"  - Evidence: `{evidence_preview}`")
                    if f["suggestion"]:
                        lines.append(f"  - Suggestion: {f['suggestion']}")
                lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Generated by [Site Audit Agent (SAA)](https://github.com/trustworthyagents/saa)*")

    return "\n".join(lines)
