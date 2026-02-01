# Default Website Audit Plan

This is a baseline audit plan for any website. Adapt based on mode: For own sites (--mode own), perform deep dives with full compliance checks and issue flagging. For competitors (--mode competitor), focus on light scans for learnings—highlight strengths, innovations, and ideas we might adopt, ignoring absences or minor flaws. Crawl starting from the base URL: depth 3 for own (thorough), depth 1 for competitors (quick). Pace requests to mimic human browsing (1-5s delays). For each page, collect evidence (e.g., code snippets, metrics) and prioritize high-impact findings.

## Base URL
[Specify the site URL here, e.g., https://your-site.com or https://competitor.com]. If not provided, prompt the user.

## [Both] General Site Overview
- Infer site type (e.g., e-commerce, blog) from structure/content.
- Detect tech stack (e.g., CMS, frameworks) via headers/source.
- Note overall performance (load time <3s ideal) and mobile-friendliness.
- For competitors: Highlight clever tech choices (e.g., "Uses Next.js for fast SSR—potential for our perf gains").

## [Both] SEO Checks
- Check HTTPS usage, meta tags (title/description), canonicals, URL structure.
- [Own: Deep] Flag issues like mixed content, duplicate metas, broken links (scan all).
- [Competitor: Learning] Note effective strategies (e.g., "Keyword-rich URLs boost visibility—idea: Refine ours similarly").

## [Both] Structured Data and Schema Checks
- Detect schema.org/JSON-LD (e.g., Organization, Product, FAQ).
- [Own: Deep] Validate fully, flag errors/misses (e.g., no rich snippets).
- [Competitor: Learning] Spotlight innovative uses (e.g., "Custom schema for interactive polls—consider for user engagement").

## [Both] Open Graph (OG) and Social Sharing Checks
- Verify OG metas (title, description, image, url).
- [Own: Deep] Ensure images load, sized right (1200x630px), optimized; flag gaps.
- [Competitor: Learning] Praise strong previews (e.g., "Vivid OG images drive shares—idea: Test similar visuals").

## [Both] Image Optimization Checks
- Scan images for alt text, sizes, formats.
- [Own: Deep] Flag large (>500KB), non-WebP/AVIF, missing alts; suggest conversions.
- [Competitor: Learning] Admire efficiencies (e.g., "AVIF usage cuts load 30%—explore for our media-heavy pages").

## [Both] Performance Checks
- Measure load times, Core Web Vitals (LCP <2.5s, etc.).
- [Own: Deep] Identify all bottlenecks (JS/CSS, third-parties); recommend fixes.
- [Competitor: Learning] Note standout optimizations (e.g., "CDN + compression = sub-2s loads—benchmark against ours").

## [Own: Deep] Accessibility Checks (WCAG Basics)
- Check contrast, headings, ARIA, keyboard nav, form labels.
- Flag all non-compliance for fixes.

## [Own: Deep] Security Checks
- Cert validity, mixed content, cookie flags, vuln indicators.
- Alert on risks.

## [Both] User Experience (UX) Checks
- Evaluate navigation, readability, content scanability.
- [Own: Deep] Flag UX pains (e.g., intrusive pop-ups).
- [Competitor: Learning] Highlight delights (e.g., "Smooth infinite scroll—idea for our blog").

## [Both] AI Readiness Checks
- Assess E-E-A-T (author bios, sources), content for AI/voice search.
- [Own: Deep] Ensure compliance for future-proofing.
- [Competitor: Learning] Spot AI-savvy tactics (e.g., "Structured FAQs for featured snippets—adopt for traffic").

## Report Inclusions
- For own: Prioritized issues/suggestions (high/medium/low impact).
- For competitors: "What They're Doing Well" and "Ideas to Borrow" sections.
- Overall: Actionable, evidence-based; include benchmarks where relevant.
