#!/usr/bin/env python3
"""
Prepare podcast data in manageable chunks for Claude Code to process.
Breaks large JSON into smaller episode files that Claude can handle.
"""

import json
import os
from pathlib import Path

def prepare_chunks(input_file, output_dir):
    """Break podcasts.json into individual episode files."""

    # Read the full JSON
    with open(input_file, 'r') as f:
        episodes = json.load(f)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Clean any old files
    for old_file in output_path.glob("episode_*.json"):
        old_file.unlink()

    # Categorize episodes
    full_episodes = []
    quick_hits = []

    for ep in episodes:
        if not ep.get('has_transcript'):
            continue

        transcript_len = len(ep.get('transcript', ''))
        if transcript_len >= 5000:
            full_episodes.append(ep)
        elif transcript_len > 0:
            quick_hits.append(ep)

    # Sort by length (longest first)
    full_episodes.sort(key=lambda x: len(x.get('transcript', '')), reverse=True)
    quick_hits.sort(key=lambda x: len(x.get('transcript', '')), reverse=True)

    # Save metadata summary
    metadata = {
        'total_episodes': len(episodes),
        'full_episodes_count': len(full_episodes),
        'quick_hits_count': len(quick_hits),
        'full_episodes': [],
        'quick_hits': []
    }

    # Save individual full episodes
    for idx, ep in enumerate(full_episodes, 1):
        # For very long transcripts, split into sections
        transcript = ep.get('transcript', '')
        transcript_len = len(transcript)

        # If transcript is huge (>50K chars), create a condensed version
        if transcript_len > 50000:
            # Take first 20K, middle 20K, and last 10K
            condensed = (
                transcript[:20000] +
                "\n\n[...MIDDLE SECTION OMITTED...]\n\n" +
                transcript[transcript_len//2 - 10000:transcript_len//2 + 10000] +
                "\n\n[...SECTION OMITTED...]\n\n" +
                transcript[-10000:]
            )
            ep_data = {
                **ep,
                'transcript_original_length': transcript_len,
                'transcript': condensed,
                'note': f'Transcript condensed from {transcript_len:,} to ~50K chars'
            }
        else:
            ep_data = ep

        filename = f"episode_{idx:02d}_full.json"
        filepath = output_path / filename

        with open(filepath, 'w') as f:
            json.dump(ep_data, f, indent=2)

        metadata['full_episodes'].append({
            'file': filename,
            'title': ep.get('title', 'Untitled')[:80],
            'podcast': ep.get('podcast_name', 'Unknown'),
            'length': transcript_len,
            'url': ep.get('url', '')
        })

    # Save all quick hits in one file (they're small)
    if quick_hits:
        quick_hits_file = output_path / "quick_hits_all.json"
        with open(quick_hits_file, 'w') as f:
            json.dump(quick_hits, f, indent=2)

        for ep in quick_hits:
            metadata['quick_hits'].append({
                'title': ep.get('title', 'Untitled')[:80],
                'podcast': ep.get('podcast_name', 'Unknown'),
                'length': len(ep.get('transcript', '')),
                'url': ep.get('url', '')
            })

    # Save metadata
    with open(output_path / "_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    return metadata

if __name__ == "__main__":
    import sys

    # Default paths
    input_file = sys.argv[1] if len(sys.argv) > 1 else "podcasts.json"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/podcast_chunks"

    print(f"📂 Reading: {input_file}")
    print(f"📁 Output to: {output_dir}")
    print()

    metadata = prepare_chunks(input_file, output_dir)

    print("✅ Chunks prepared!")
    print()
    print(f"📊 Summary:")
    print(f"   Total episodes: {metadata['total_episodes']}")
    print(f"   Full episodes: {metadata['full_episodes_count']}")
    print(f"   Quick hits: {metadata['quick_hits_count']}")
    print()
    print(f"📁 Files created in: {output_dir}")
    print(f"   • _metadata.json (overview)")
    print(f"   • episode_XX_full.json (one per full episode)")
    print(f"   • quick_hits_all.json (all quick hits)")
    print()
    print("🎯 Next: Tell Claude to read _metadata.json to start processing!")
