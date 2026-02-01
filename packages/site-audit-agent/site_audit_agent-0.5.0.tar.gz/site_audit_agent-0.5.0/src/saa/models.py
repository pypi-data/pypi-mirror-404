"""Pydantic models for SAA data structures."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


class Severity(str, Enum):
    """Finding severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImageData(BaseModel):
    """Data about an image on a page."""
    src: str
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None  # bytes, if available
    format: Optional[str] = None  # jpg, png, webp, avif, etc.


class LinkData(BaseModel):
    """Data about a link on a page."""
    href: str
    text: str = ""
    is_internal: bool = False
    is_broken: Optional[bool] = None  # None = not checked yet


class MetaTag(BaseModel):
    """A meta tag from the page."""
    name: Optional[str] = None
    property: Optional[str] = None
    content: str = ""


class OpenGraphData(BaseModel):
    """Open Graph metadata."""
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    site_name: Optional[str] = None


class PageData(BaseModel):
    """Extracted data from a single page."""
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    canonical: Optional[str] = None

    # Content
    h1_tags: list[str] = Field(default_factory=list)
    text_content: str = ""  # Visible text, truncated

    # Meta
    meta_tags: list[MetaTag] = Field(default_factory=list)
    og_data: Optional[OpenGraphData] = None

    # Links and images
    links: list[LinkData] = Field(default_factory=list)
    images: list[ImageData] = Field(default_factory=list)

    # Technical
    is_https: bool = False
    load_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    content_type: Optional[str] = None

    # Schema/structured data
    schema_types: list[str] = Field(default_factory=list)  # e.g., ["Organization", "Product"]

    # Crawl metadata
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
    depth: int = 0
    error: Optional[str] = None


class Finding(BaseModel):
    """A single audit finding/issue."""
    check_name: str
    severity: Severity
    message: str
    url: str  # The page this finding relates to
    evidence: Optional[str] = None  # Code snippet, metric, etc.
    suggestion: Optional[str] = None  # How to fix


class CheckResult(BaseModel):
    """Result from running a check on page(s)."""
    check_name: str
    findings: list[Finding] = Field(default_factory=list)
    pages_checked: int = 0


class AuditResult(BaseModel):
    """Complete audit result."""
    url: str
    mode: str  # "own" or "competitor"
    started_at: datetime
    completed_at: Optional[datetime] = None
    pages: list[PageData] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)

    # Summary stats
    total_pages: int = 0
    total_images: int = 0
    total_links: int = 0
    issues_by_severity: dict[str, int] = Field(default_factory=dict)
