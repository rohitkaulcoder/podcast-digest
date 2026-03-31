#!/usr/bin/env python3
"""
Generate Digest HTML from Highlights JSON
==========================================
Reads highlights_YYYY-MM-DD.json and produces a clean HTML digest page.

Usage:
    python generate_digest_html.py                              # Today's date
    python generate_digest_html.py --date 2026-03-30
    python generate_digest_html.py --input highlights.json --output digest.html
"""

import argparse
import html
import json
import os
import sys
from datetime import datetime


def generate_html(highlights_data: list, date_str: str) -> str:
    """Generate a clean HTML digest from highlights JSON."""

    episode_count = len(highlights_data)
    total_highlights = sum(len(ep["highlights"]) for ep in highlights_data)

    episodes_html = []
    for ep in highlights_data:
        title = html.escape(ep["episode"]["title"])
        podcast = html.escape(ep["episode"]["podcast"])
        url = ep["episode"].get("url", "")

        highlights_html = []
        for h in ep["highlights"]:
            speaker = html.escape(h.get("speaker", ""))
            text = html.escape(h["text"]).replace("\n\n", "</p><p>").replace("\n", "<br>")
            speaker_line = f'<div class="speaker">{speaker}</div>' if speaker else ""
            highlights_html.append(f"""            <div class="highlight">
                {speaker_line}
                <p>{text}</p>
            </div>""")

        link_html = f' &middot; <a href="{html.escape(url)}">Listen</a>' if url else ""
        episodes_html.append(f"""    <div class="episode">
        <h2>{title}</h2>
        <div class="meta">{podcast}{link_html}</div>
{chr(10).join(highlights_html)}
    </div>""")

    # Format date
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("%B %d, %Y")
    except ValueError:
        formatted_date = date_str

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Podcast Digest - {formatted_date}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7; color: #2D2D2D;
            background: #fff;
            padding: 40px 20px;
        }}
        .container {{ max-width: 780px; margin: 0 auto; }}
        header {{ padding-bottom: 24px; margin-bottom: 40px; border-bottom: 2px solid #eee; }}
        h1 {{ font-size: 1.8rem; font-weight: 700; color: #111; }}
        .date-line {{ color: #888; font-size: 0.95rem; margin-top: 4px; }}
        .episode {{ margin-bottom: 50px; }}
        .episode h2 {{ font-size: 1.25rem; font-weight: 700; color: #111; line-height: 1.35; }}
        .meta {{ color: #888; font-size: 0.85rem; margin: 4px 0 20px; }}
        .meta a {{ color: #555; }}
        .highlight {{
            margin: 16px 0;
            padding: 16px 20px;
            background: #fafafa;
            border-left: 3px solid #ddd;
            border-radius: 4px;
        }}
        .highlight .speaker {{
            font-size: 0.8rem;
            font-weight: 600;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 8px;
        }}
        .highlight p {{
            font-size: 0.92rem;
            color: #444;
            line-height: 1.7;
        }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 40px 0; }}
        footer {{ text-align: center; color: #ccc; font-size: 0.8rem; padding: 30px 0; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>Podcast Digest</h1>
        <div class="date-line">{formatted_date} &mdash; {episode_count} episodes, {total_highlights} highlights</div>
    </header>

{(chr(10) + "    <hr>" + chr(10)).join(episodes_html)}

    <footer>Generated with Claude Code</footer>
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate digest HTML from highlights JSON")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--input", type=str, help="Input highlights JSON")
    parser.add_argument("--output", type=str, help="Output HTML file")

    args = parser.parse_args()
    work_dir = "/Users/rohitkaul/Projects/podcast-digest"

    input_file = args.input or f"{work_dir}/highlights_{args.date}.json"
    output_file = args.output or f"{work_dir}/digest_{args.date}.html"

    if not os.path.exists(input_file):
        print(f"No highlights file found: {input_file}")
        sys.exit(1)

    with open(input_file) as f:
        data = json.load(f)

    html_content = generate_html(data, args.date)

    with open(output_file, "w") as f:
        f.write(html_content)

    episode_count = len(data)
    highlight_count = sum(len(ep["highlights"]) for ep in data)
    print(f"Generated {output_file} ({episode_count} episodes, {highlight_count} highlights)")

    # Update index.html with new digest link
    update_index(work_dir, args.date, episode_count, highlight_count)


def update_index(work_dir: str, date_str: str, episode_count: int, highlight_count: int):
    """Add today's digest to the top of index.html."""
    index_path = f"{work_dir}/index.html"
    if not os.path.exists(index_path):
        return

    with open(index_path) as f:
        index_html = f.read()

    # Check if already linked
    digest_filename = f"digest_{date_str}.html"
    if digest_filename in index_html:
        return

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("%B %d, %Y")
    except ValueError:
        formatted_date = date_str

    ep_label = "episode" if episode_count == 1 else "episodes"

    new_card = f"""                <li>
                    <div class="digest-card">
                        <a href="{digest_filename}" class="digest-link">
                            <div class="date">{formatted_date}</div>
                            <div class="stats">
                                <span class="stat-badge">📊 <strong>{episode_count}</strong> {ep_label}</span>
                                <span class="stat-badge">💡 <strong>{highlight_count}</strong> highlights</span>
                            </div>
                        </a>
                    </div>
                </li>
"""

    # Insert after <ul class="digest-grid">
    marker = '<ul class="digest-grid">'
    idx = index_html.find(marker)
    if idx >= 0:
        insert_pos = idx + len(marker) + 1  # after the newline
        index_html = index_html[:insert_pos] + new_card + index_html[insert_pos:]

        with open(index_path, "w") as f:
            f.write(index_html)
        print(f"Updated index.html with {digest_filename}")


if __name__ == "__main__":
    main()
