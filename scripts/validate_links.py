#!/usr/bin/env python3
"""Tutorial Link Validator for build-your-own-x repository.

Validates all tutorial links in README.md, checking for dead links,
categorizing results, and suggesting archive.org fallbacks.
"""

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


# default config
DEFAULT_TIMEOUT = 10
DEFAULT_MAX_WORKERS = 10
DEFAULT_CACHE_FILE = ".link_cache.json"
USER_AGENT = "Mozilla/5.0 (build-your-own-x link checker)"
ARCHIVE_ORG_PREFIX = "https://web.archive.org/web/"


@dataclass
class LinkResult:
    """Result of checking a single link."""
    url: str
    status_code: int
    is_alive: bool
    category: str
    line_number: int
    error: Optional[str] = None
    archive_url: Optional[str] = None
    response_time: float = 0.0


@dataclass
class ValidationReport:
    """Overall validation report."""
    total_links: int = 0
    alive_links: int = 0
    dead_links: int = 0
    skipped_links: int = 0
    errors: int = 0
    results: List[LinkResult] = field(default_factory=list)
    categories: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    start_time: float = 0.0
    end_time: float = 0.0


class LinkCache:
    """Cache for link check results to avoid re-checking."""

    def __init__(self, cache_file: str = DEFAULT_CACHE_FILE):
        self.cache_file = cache_file
        self.cache: Dict[str, dict] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.cache = {}

    def save(self):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def _key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str, max_age: int = 86400) -> Optional[dict]:
        key = self._key(url)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry.get("timestamp", 0) < max_age:
                return entry
        return None

    def set(self, url: str, result: dict):
        key = self._key(url)
        result["timestamp"] = time.time()
        self.cache[key] = result


def extract_markdown_links(text: str) -> List[Tuple[str, str, int]]:
    """Extract all markdown links with their text and line numbers."""
    links = []
    for line_num, line in enumerate(text.splitlines(), 1):
        # Match [text](url) pattern
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
            link_text = match.group(1)
            url = match.group(2)
            if url.startswith(("http://", "https://")):
                links.append((link_text, url, line_num))
    return links


def extract_categories(text: str) -> Dict[str, List[Tuple[str, str, int]]]:
    """Parse README.md to extract links organized by category."""
    categories = defaultdict(list)
    current_category = "Uncategorized"

    for line_num, line in enumerate(text.splitlines(), 1):
        # Detect category headers (## Build your own ...)
        header_match = re.match(r'^#{1,3}\s+(.+)', line)
        if header_match:
            current_category = header_match.group(1).strip()
            continue

        # Extract links in current category
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
            link_text = match.group(1)
            url = match.group(2)
            if url.startswith(("http://", "https://")):
                categories[current_category].append((link_text, url, line_num))

    return dict(categories)


def check_single_link(url: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[int, bool, Optional[str], float]:
    """Check if a single URL is alive. Returns (status_code, is_alive, error, response_time)."""
    start = time.time()
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - start
            return resp.status, True, None, elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        return e.code, False, str(e.reason), elapsed
    except urllib.error.URLError as e:
        elapsed = time.time() - start
        return 0, False, str(e.reason), elapsed
    except Exception as e:
        elapsed = time.time() - start
        return 0, False, str(e), elapsed


def get_archive_url(url: str) -> Optional[str]:
    """Generate an archive.org fallback URL."""
    encoded = urllib.parse.quote(url, safe="")
    return f"{ARCHIVE_ORG_PREFIX}{encoded}"


def check_link_with_cache(
    url: str,
    category: str,
    line_number: int,
    cache: LinkCache,
    timeout: int = DEFAULT_TIMEOUT,
) -> LinkResult:
    """Check a link, using cache if available."""
    cached = cache.get(url)
    if cached:
        return LinkResult(
            url=url,
            status_code=cached.get("status_code", 0),
            is_alive=cached.get("is_alive", False),
            category=category,
            line_number=line_number,
            error=cached.get("error"),
            archive_url=cached.get("archive_url"),
            response_time=cached.get("response_time", 0.0),
        )

    status_code, is_alive, error, response_time = check_single_link(url, timeout)
    archive_url = None if is_alive else get_archive_url(url)

    result = LinkResult(
        url=url,
        status_code=status_code,
        is_alive=is_alive,
        category=category,
        line_number=line_number,
        error=error,
        archive_url=archive_url,
        response_time=response_time,
    )

    cache.set(url, {
        "status_code": status_code,
        "is_alive": is_alive,
        "error": error,
        "archive_url": archive_url,
        "response_time": response_time,
    })

    return result


def validate_links(
    readme_path: str,
    max_workers: int = DEFAULT_MAX_WORKERS,
    timeout: int = DEFAULT_TIMEOUT,
    cache_file: str = DEFAULT_CACHE_FILE,
    verbose: bool = False,
) -> ValidationReport:
    """Validate all links in a README file."""
    report = ValidationReport(start_time=time.time())

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    categories = extract_categories(content)
    cache = LinkCache(cache_file)

    # Flatten all links with their categories
    all_links = []
    for cat, links in categories.items():
        for text, url, line_num in links:
            all_links.append((url, cat, line_num))
            report.categories[cat] = report.categories.get(cat, 0) + 1

    report.total_links = len(all_links)
    checked = 0

    if verbose:
        print(f"Found {report.total_links} links across {len(categories)} categories")

    # Check links concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_link_with_cache, url, cat, line_num, cache, timeout): (url, cat, line_num)
            for url, cat, line_num in all_links
        }

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            report.results.append(result)

            if result.is_alive:
                report.alive_links += 1
            elif result.error:
                report.errors += 1
                report.dead_links += 1
            else:
                report.dead_links += 1

            checked += 1
            if verbose and checked % 10 == 0:
                print(f"Progress: {checked}/{report.total_links} links checked")

    cache.save()
    report.end_time = time.time()
    return report


def print_report(report: ValidationReport):
    """Print a formatted validation report."""
    duration = report.end_time - report.start_time
    print("\n" + "=" * 60)
    print("LINK VALIDATION REPORT")
    print("=" * 60)
    print(f"Total links checked: {report.total_links}")
    print(f"Alive: {report.alive_links}")
    print(f"Dead:  {report.dead_links}")
    print(f"Errors: {report.errors}")
    print(f"Duration: {duration:.1f}s")
    print()

    # Print categories summary
    print("Categories:")
    for cat, count in sorted(report.categories.items()):
        print(f"  {cat}: {count} links")
    print()

    # Print dead links
    dead = [r for r in report.results if not r.is_alive]
    if dead:
        print("Dead Links:")
        for r in dead:
            print(f"  Line {r.line_number}: {r.url}")
            print(f"    Status: {r.status_code} | Error: {r.error}")
            if r.archive_url:
                print(f"    Archive: {r.archive_url}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate tutorial links in README.md")
    parser.add_argument("readme", nargs="?", default="README.md", help="Path to README.md")
    parser.add_argument("--workers", type=int, default=DEFAULT_MAX_WORKERS, help="Max concurrent workers")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument("--cache-file", default=DEFAULT_CACHE_FILE, help="Cache file path")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json-output", help="Write results as JSON to file")
    args = parser.parse_args()

    if not os.path.exists(args.readme):
        print(f"Error: {args.readme} not found", file=sys.stderr)
        sys.exit(1)

    cache_file = args.cache_file if not args.no_cache else None
    if cache_file is None:
        cache_file = os.devnull

    report = validate_links(
        args.readme,
        max_workers=args.workers,
        timeout=args.timeout,
        cache_file=cache_file,
        verbose=args.verbose,
    )

    print_report(report)

    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump({
                "total": report.total_links,
                "alive": report.alive_links,
                "dead": report.dead_links,
                "errors": report.errors,
                "results": [asdict(r) for r in report.results],
            }, f, indent=2)
        print(f"JSON report written to {args.json_output}")

    sys.exit(1 if report.dead_links > 0 else 0)


if __name__ == "__main__":
    main()
