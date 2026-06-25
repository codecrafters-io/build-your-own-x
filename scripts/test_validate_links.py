#!/usr/bin/env python3
"""Tests for validate_links.py"""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from validate_links import (
    extract_markdown_links,
    extract_categories,
    check_single_link,
    get_archive_url,
    LinkCache,
    LinkResult,
    ValidationReport,
    validate_links,
)


class TestExtractMarkdownLinks:
    def test_basic_link(self):
        text = "[Example](https://example.com)"
        links = extract_markdown_links(text)
        assert len(links) == 1
        assert links[0] == ("Example", "https://example.com", 1)

    def test_multiple_links(self):
        text = "[A](https://a.com)\n[B](https://b.com)"
        links = extract_markdown_links(text)
        assert len(links) == 2

    def test_ignores_non_http(self):
        text = "[Local](./local.md)"
        links = extract_markdown_links(text)
        assert len(links) == 0

    def test_preserves_line_numbers(self):
        text = "line1\n[Link](https://x.com)\nline3"
        links = extract_markdown_links(text)
        assert links[0][2] == 2

    def test_multiple_links_per_line(self):
        text = "[A](https://a.com) and [B](https://b.com)"
        links = extract_markdown_links(text)
        assert len(links) == 2


class TestExtractCategories:
    def test_categorizes_links(self):
        text = "## Web Server\n[Link](https://x.com)\n## Database\n[DB](https://db.com)"
        cats = extract_categories(text)
        assert "Web Server" in cats
        assert "Database" in cats

    def test_uncategorized(self):
        text = "[Link](https://x.com)"
        cats = extract_categories(text)
        assert "Uncategorized" in cats


class TestGetArchiveUrl:
    def test_generates_archive_url(self):
        url = "https://example.com/page"
        result = get_archive_url(url)
        assert result.startswith("https://web.archive.org/web/")
        assert "example.com" in result


class TestLinkCache:
    def test_set_and_get(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            cache = LinkCache(f.name)
            cache.set("https://example.com", {"status_code": 200, "is_alive": True})
            result = cache.get("https://example.com")
            assert result is not None
            assert result["status_code"] == 200
            os.unlink(f.name)

    def test_cache_miss(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            cache = LinkCache(f.name)
            result = cache.get("https://nonexistent.com")
            assert result is None
            os.unlink(f.name)

    def test_save_and_reload(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
        cache = LinkCache(path)
        cache.set("https://test.com", {"status_code": 200, "is_alive": True})
        cache.save()
        cache2 = LinkCache(path)
        result = cache2.get("https://test.com")
        assert result is not None
        os.unlink(path)


class TestLinkResult:
    def test_creation(self):
        r = LinkResult(url="https://x.com", status_code=200, is_alive=True, category="Test", line_number=1)
        assert r.is_alive is True
        assert r.error is None

    def test_dead_link(self):
        r = LinkResult(url="https://x.com", status_code=404, is_alive=False, category="Test", line_number=1, error="Not Found")
        assert r.is_alive is False


class TestValidationReport:
    def test_defaults(self):
        r = ValidationReport()
        assert r.total_links == 0
        assert r.alive_links == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
