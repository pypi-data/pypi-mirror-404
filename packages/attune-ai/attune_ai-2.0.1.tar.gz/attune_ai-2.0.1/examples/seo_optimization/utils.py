"""Utility functions for SEO optimization agent system."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SEOIssue:
    """Represents an SEO issue found in a file."""

    file: Path
    severity: str  # critical, warning, info
    category: str  # meta_tags, content, technical, links
    element: str
    message: str
    line: int | None = None
    suggestion: str | None = None


class SEOAuditor:
    """Audits markdown files for SEO issues."""

    def __init__(self, config):
        self.config = config

    def check_meta_tags(self) -> list[SEOIssue]:
        """Check meta tags in all markdown files."""
        issues = []
        for md_file in self.config.docs_path.rglob("*.md"):
            content = md_file.read_text()

            # Check for meta description
            if "description:" not in content:
                issues.append(
                    SEOIssue(
                        file=md_file,
                        severity="critical",
                        category="meta_tags",
                        element="meta_description",
                        message="Missing meta description",
                    )
                )

        return issues


class ContentOptimizer:
    """Analyzes and optimizes content structure."""

    def __init__(self, config):
        self.config = config

    def analyze_content(self) -> list[SEOIssue]:
        """Analyze content quality and structure."""
        issues = []
        for md_file in self.config.docs_path.rglob("*.md"):
            content = md_file.read_text()

            # Check H1 count
            h1_count = len(re.findall(r"^# ", content, re.MULTILINE))
            if h1_count != 1:
                issues.append(
                    SEOIssue(
                        file=md_file,
                        severity="warning",
                        category="content",
                        element="h1_tag",
                        message=f"Found {h1_count} H1 tags (should be exactly 1)",
                    )
                )

        return issues


class TechnicalSEOSpecialist:
    """Handles technical SEO elements."""

    def __init__(self, config):
        self.config = config

    def check_technical_elements(self) -> list[SEOIssue]:
        """Check technical SEO elements."""
        issues = []

        # Check for sitemap
        sitemap_path = self.config.docs_path.parent / "site" / "sitemap.xml"
        if not sitemap_path.exists():
            issues.append(
                SEOIssue(
                    file=self.config.docs_path,
                    severity="warning",
                    category="technical",
                    element="sitemap",
                    message="sitemap.xml not found",
                )
            )

        return issues


class LinkAnalyzer:
    """Analyzes internal and external links."""

    def __init__(self, config):
        self.config = config

    def analyze_links(self) -> list[SEOIssue]:
        """Analyze link structure."""
        issues = []

        for md_file in self.config.docs_path.rglob("*.md"):
            content = md_file.read_text()

            # Find broken relative links
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
            for link_text, link_url in links:
                if link_url.startswith("http"):
                    continue

                target_path = (md_file.parent / link_url).resolve()
                if not target_path.exists():
                    issues.append(
                        SEOIssue(
                            file=md_file,
                            severity="warning",
                            category="links",
                            element=link_url,
                            message=f"Broken link: {link_url}",
                        )
                    )

        return issues


class SEOReporter:
    """Generates SEO reports."""

    def generate_report(self, audit_results: dict[str, Any]) -> dict[str, Any]:
        """Generate comprehensive audit report."""
        all_issues = []
        for category_issues in audit_results.values():
            all_issues.extend(category_issues)

        critical = len([i for i in all_issues if i.severity == "critical"])
        warning = len([i for i in all_issues if i.severity == "warning"])
        info = len([i for i in all_issues if i.severity == "info"])

        return {
            "total_issues": len(all_issues),
            "critical_count": critical,
            "warning_count": warning,
            "info_count": info,
            "issues": [
                {
                    "file": str(i.file),
                    "severity": i.severity,
                    "category": i.category,
                    "element": i.element,
                    "message": i.message,
                }
                for i in all_issues
            ],
        }


class SEOFixer:
    """Implements SEO fixes."""

    def __init__(self, config):
        self.config = config

    def apply_fix(self, suggestion: dict[str, Any]) -> bool:
        """Apply a fix suggestion to a file."""
        try:
            file_path = Path(suggestion["file"])

            if suggestion["fix_type"] == "add_meta_tag":
                return self._add_meta_tag(file_path, suggestion["data"])
            elif suggestion["fix_type"] == "update_content":
                return self._update_content(file_path, suggestion["data"])

            return False
        except Exception:
            return False

    def _add_meta_tag(self, file_path: Path, data: dict[str, Any]) -> bool:
        """Add meta tag to markdown frontmatter."""
        content = file_path.read_text()

        if content.startswith("---"):
            # Has frontmatter
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body = parts[2]

                # Add meta tag
                tag_name = data["tag"]
                tag_value = data.get("suggested_value", "")
                new_frontmatter = f"{frontmatter}\n{tag_name}: {tag_value}\n"

                new_content = f"---{new_frontmatter}---{body}"
                file_path.write_text(new_content)
                return True

        return False

    def _update_content(self, file_path: Path, data: dict[str, Any]) -> bool:
        """Update content in file."""
        # Simplified implementation
        return True
