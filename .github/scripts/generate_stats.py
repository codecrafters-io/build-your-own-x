#!/usr/bin/env python3
"""
Generate language statistics from README.md and create a visualization in STATS-main.md
"""

import re
from collections import Counter
from typing import Dict, List, Tuple

def extract_languages_from_readme(filename: str = 'README.md') -> List[str]:
    """Extract all programming languages mentioned in project entries."""
    languages = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match: * [**Language**: _Title_](url)
    # Handles multiple languages separated by / or ,
    pattern = r'^\* \[\*\*([^*]+)\*\*:'

    matches = re.findall(pattern, content, re.MULTILINE)
    
    for match in matches:
        # Split by / or , and clean up whitespace
        langs = re.split(r'\s*/\s*|\s*,\s*', match)
        for lang in langs:
            lang = lang.strip()
            if lang:
                languages.append(lang)
    
    return languages

def normalize_language(lang: str) -> str:
    """Normalize language names for consistency."""
    # Handle common variations
    normalizations = {
        'Node.js': 'JavaScript'
    }
    return normalizations.get(lang, lang)

def count_languages(languages: List[str]) -> Dict[str, int]:
    """Count occurrences of each language."""
    normalized = [normalize_language(lang) for lang in languages]
    return dict(Counter(normalized))

def create_horizontal_bar(count: int, max_count: int, bar_width: int = 50) -> str:
    """Create a horizontal bar for visualization."""
    filled = int((count / max_count) * bar_width)
    bar = '█' * filled + '░' * (bar_width - filled)
    return bar

def generate_stats_markdown(language_counts: Dict[str, int], num_projects: int) -> str:
    """Generate the markdown content for STATS-main.md."""
    # Sort by count (descending) then by name
    sorted_langs = sorted(language_counts.items(), key=lambda x: (-x[1], x[0]))
    
    total_language_mentions = sum(language_counts.values())
    max_count = max(language_counts.values())
    
    # Separate languages >= 1% and < 1%
    threshold = num_projects * 0.01  # 1% threshold
    main_langs = []
    other_langs = []
    
    for lang, count in sorted_langs:
        if count >= threshold:
            main_langs.append((lang, count))
        else:
            other_langs.append((lang, count))
    
    # Calculate "Other" total
    other_count = sum(count for _, count in other_langs)
    
    # Build markdown content
    lines = [
        "# Build Your Own X - Language Statistics\n",
        f"**Total Projects:** {num_projects}\n",
        f"**Total Language Mentions:** {total_language_mentions} *(some projects support multiple languages)*\n",
        f"**Unique Languages:** {len(language_counts)}\n",
        f"**Last Updated:** {get_current_date()}\n",
        "---\n",
        "## Language Distribution\n",
        "| Language | Count | Percentage | Distribution |",
        "|----------|-------|------------|--------------|"
    ]
    
    for lang, count in main_langs:
        percentage = (count / num_projects) * 100
        bar = create_horizontal_bar(count, max_count, 30)
        lines.append(f"| {lang} | {count} | {percentage:.1f}% | {bar} |")
    
    # Add "Other" category if there are languages < 1%
    if other_langs:
        percentage = (other_count / num_projects) * 100
        bar = create_horizontal_bar(other_count, max_count, 30)
        lines.append(f"| Other* | {other_count} | {percentage:.1f}% | {bar} |")
    
    lines.append("\n---\n")
    lines.append("## Top 10 Languages\n")
    
    for i, (lang, count) in enumerate(sorted_langs[:10], 1):
        percentage = (count / num_projects) * 100
        lines.append(f"{i}. **{lang}**: {count} projects ({percentage:.1f}%)")
    
    # Add footnote for "Other" languages
    if other_langs:
        lines.append("## Footnotes\n")
        lines.append(f"**\\* Other languages** (each < 1% of total projects): ")
        other_names = [f"{lang} ({count})" for lang, count in sorted(other_langs, key=lambda x: (-x[1], x[0]))]
        lines.append(", ".join(other_names))
    
    return '\n'.join(lines) + '\n'

def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d')

def count_projects(filename: str = 'README.md') -> int:
    """Count the actual number of project entries."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r'^\* \[\*\*([^*]+)\*\*:'
    matches = re.findall(pattern, content, re.MULTILINE)
    return len(matches)

def main():
    print("Analyzing README.md...")
    num_projects = count_projects()
    print(f"Found {num_projects} project entries")
    
    languages = extract_languages_from_readme()
    print(f"Extracted {len(languages)} language mentions (some projects list multiple languages)")
    
    language_counts = count_languages(languages)
    print(f"Detected {len(language_counts)} unique languages")
    
    print("\nGenerating STATS-main.md...")
    stats_content = generate_stats_markdown(language_counts, num_projects)
    
    with open('STATS-main.md', 'w', encoding='utf-8') as f:
        f.write(stats_content)
    
    print("✓ STATS-main.md generated successfully!")
    print(f"\nTop 5 languages:")
    sorted_langs = sorted(language_counts.items(), key=lambda x: -x[1])
    for lang, count in sorted_langs[:5]:
        print(f"  - {lang}: {count}")

if __name__ == '__main__':
    main()
