#!/usr/bin/env python3
"""
Push Podcast Highlights to Readwise
====================================
Reads podcasts.json (transcripts), generates highlights via Claude,
and pushes them to Readwise.

Usage:
    python push_to_readwise.py                          # Use ~/podcasts.json
    python push_to_readwise.py --input episodes.json    # Custom input
    python push_to_readwise.py --dry-run                # Generate but don't push
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile


HIGHLIGHT_PROMPT = """Read the podcast transcript below and extract 10-15 highlights.

Each highlight should be a cleaned-up version of the speaker's actual words — NOT a summary or essay rewrite. Your job is to be an editor, not a writer. Specifically:

- PRESERVE the speaker's actual words, phrasing, metaphors, and specific examples as much as possible
- CUT filler words (like, you know, I mean, basically, obviously), false starts, self-corrections, and interviewer interjections
- ADD paragraph breaks for readability
- DO NOT rephrase their ideas into generic essay prose
- DO NOT summarize — keep the detail, the specific numbers, the anecdotes, the quotes within quotes
- Each highlight should capture one complete idea arc (3-5 paragraphs)
- It should feel like reading a cleaned-up transcript where the speaker is talking directly to you

For each highlight, identify the speaker (host or guest). Use the episode title and context to determine speaker names.

Output as a JSON array. Each element has two keys: "speaker" (string) and "text" (string with the cleaned-up highlight).

Only output the JSON, nothing else. Skip any ad reads or sponsor segments.

EPISODE: __TITLE__
PODCAST: __PODCAST__

TRANSCRIPT:
__TRANSCRIPT__"""


def generate_highlights(episode: dict) -> list:
    """Generate highlights for an episode using Claude."""
    title = episode["title"]
    podcast = episode["podcast"]
    transcript = episode["transcript"]

    # Skip HTML content (false positive RSS transcript detection)
    if transcript.strip().startswith("<!DOCTYPE") or transcript.strip().startswith("<html"):
        print(f"    ⚠ Transcript is HTML, not text — skipping")
        return []

    # Truncate very long transcripts to avoid token limits
    # Claude --print has tighter limits; 80K chars is ~20K tokens which is safe
    if len(transcript) > 80000:
        transcript = transcript[:80000]

    prompt = HIGHLIGHT_PROMPT.replace("__TITLE__", title).replace("__PODCAST__", podcast).replace("__TRANSCRIPT__", transcript)

    # Write prompt to temp file to avoid shell escaping issues
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        with open(prompt_file) as pf:
            prompt_text = pf.read()

        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions"],
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            print(f"    ✗ Claude error: {result.stderr[:200]}")
            return []

        raw = result.stdout.strip()
        # Strip markdown code fences and any preamble text
        raw = raw.replace("```json", "").replace("```", "").strip()
        # Find the first '[' to skip any preamble
        bracket_idx = raw.find("[")
        if bracket_idx >= 0:
            raw = raw[bracket_idx:]
        # Find the last ']' to strip any trailing text
        rbracket_idx = raw.rfind("]")
        if rbracket_idx >= 0:
            raw = raw[:rbracket_idx + 1]
        highlights = json.loads(raw)
        return highlights

    except json.JSONDecodeError as e:
        print(f"    ✗ Failed to parse Claude output as JSON: {e}")
        return []
    except subprocess.TimeoutExpired:
        print(f"    ✗ Claude timed out")
        return []
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return []
    finally:
        os.unlink(prompt_file)


def push_to_readwise(highlights: list, episode: dict) -> bool:
    """Push highlights to Readwise via CLI."""
    title = episode["title"]
    url = episode.get("url", "")

    payload = []
    for h in highlights:
        # Prepend speaker name to highlight text
        text = f"**{h['speaker']}:** {h['text']}" if h.get("speaker") else h["text"]
        entry = {
            "text": text,
            "title": title,
            "author": episode["podcast"],
            "category": "podcasts",
            "highlight_tags": [{"name": "podcast-digest"}],
        }
        if url:
            entry["source_url"] = url
        payload.append(entry)

    try:
        result = subprocess.run(
            ["readwise", "readwise-create-highlights", "--highlights", json.dumps(payload)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            for item in data:
                print(f"    ✓ Pushed {item['num_highlights']} highlights (category={item.get('category')})")
            return True
        else:
            print(f"    ✗ Readwise error: {result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"    ✗ Readwise push error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate podcast highlights and push to Readwise")
    parser.add_argument("--input", type=str, default=os.path.expanduser("~/podcasts.json"),
                        help="Input file (default: ~/podcasts.json)")
    parser.add_argument("--dry-run", action="store_true", help="Generate highlights but don't push to Readwise")
    parser.add_argument("--save-highlights", type=str, help="Save generated highlights to JSON file")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"✗ Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input) as f:
        episodes = json.load(f)

    # Filter to episodes with transcripts
    episodes_with_transcript = [e for e in episodes if e.get("has_transcript") and e.get("transcript")]

    if not episodes_with_transcript:
        print("No episodes with transcripts found. Nothing to do.")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  PODCAST HIGHLIGHTS → READWISE")
    print(f"{'='*60}")
    print(f"Episodes with transcripts: {len(episodes_with_transcript)}")
    print()

    all_highlights = []
    total_pushed = 0

    for ep in episodes_with_transcript:
        print(f"🎙 {ep['podcast']} — {ep['title'][:60]}...")

        # Generate highlights
        print(f"  🧠 Generating highlights with Claude...")
        highlights = generate_highlights(ep)

        if not highlights:
            print(f"  ⚠ No highlights generated")
            continue

        print(f"  ✓ Generated {len(highlights)} highlights")

        all_highlights.append({
            "episode": {
                "title": ep["title"],
                "podcast": ep["podcast"],
                "url": ep.get("url", ""),
                "published_at": ep.get("published_at", ""),
            },
            "highlights": highlights,
        })

        # Push to Readwise
        if not args.dry_run:
            print(f"  📚 Pushing to Readwise...")
            if push_to_readwise(highlights, ep):
                total_pushed += len(highlights)
        else:
            print(f"  (dry run — skipping Readwise push)")

        print()

    # Save highlights if requested
    if args.save_highlights and all_highlights:
        with open(args.save_highlights, "w") as f:
            json.dump(all_highlights, f, indent=2, ensure_ascii=False)
        print(f"Highlights saved to: {args.save_highlights}")

    print(f"{'='*60}")
    print(f"DONE")
    print(f"{'='*60}")
    print(f"Episodes processed: {len(episodes_with_transcript)}")
    print(f"Total highlights generated: {sum(len(h['highlights']) for h in all_highlights)}")
    if not args.dry_run:
        print(f"Total highlights pushed to Readwise: {total_pushed}")


if __name__ == "__main__":
    main()
