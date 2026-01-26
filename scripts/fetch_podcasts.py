#!/usr/bin/env python3
"""
Podcast Transcript Fetcher
==========================
Fetches transcripts from your subscribed podcast YouTube channels.
Run this on your local machine, then share the output with Claude.

Setup:
    pip install youtube-transcript-api google-api-python-client

Usage:
    python fetch_podcasts.py                    # Fetch last 7 days
    python fetch_podcasts.py --days 14          # Fetch last 14 days
    python fetch_podcasts.py --max-per-channel 3  # Max 3 videos per channel
    python fetch_podcasts.py --output podcasts.json  # Save to file

Requirements:
    - YouTube Data API key (free, instructions below)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Optional

# Check dependencies
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("ERROR: youtube-transcript-api not installed")
    print("Run: pip install youtube-transcript-api")
    sys.exit(1)

try:
    from googleapiclient.discovery import build
except ImportError:
    print("ERROR: google-api-python-client not installed")
    print("Run: pip install google-api-python-client")
    sys.exit(1)


# =============================================================================
# CONFIGURATION - Your podcast channels
# =============================================================================

CHANNELS = [
    {"name": "Acquired / ACQ2", "handle": "AcquiredFM"},
    {"name": "BG²", "handle": "Bg2Pod"},
    {"name": "Cheeky Pint", "handle": "stripe"},
    {"name": "David Perell", "handle": "davidperell"},
    {"name": "Dialectic", "handle": "Dialectic"},
    {"name": "Dwarkesh Podcast", "handle": "DwarkeshPatel"},
    {"name": "Founders", "handle": "founderspodcast1"},
    {"name": "In Depth", "handle": "FirstRoundCapital"},
    {"name": "Infinite Loops", "handle": "infinitel88ps"},
    {"name": "Invest Like the Best", "handle": "JoinColossus"},
    {"name": "Lenny's Podcast", "handle": "lennyspodcast"},
    {"name": "No Priors", "handle": "NoPriorsPodcast"},
    {"name": "TBPN", "handle": "TBPNLive"},
    {"name": "The A16Z Show", "handle": "a16z"},
    {"name": "TiTV", "handle": "theinformation"},
    {"name": "The Knowledge Project", "handle": "tkppodcast"},
    {"name": "The Logan Bartlett Show", "channel_id": "UCugS0jD5IAdoqzjaNYzns7w"},
    {"name": "The Peel", "handle": "ThePeelPod"},
    {"name": "20VC", "handle": "20vc"},
    {"name": "Uncapped", "handle": "uncappedpod"},
    {"name": "Unsolicited Feedback", "handle": "reforgehq"},
    {"name": "Y Combinator", "handle": "ycombinator"},
    {"name": "The Generalist", "handle": "TheGeneralistPodcast"},
]


# =============================================================================
# YOUTUBE API FUNCTIONS
# =============================================================================

def get_api_key() -> str:
    """Get YouTube API key from environment or prompt user."""
    api_key = os.environ.get("YOUTUBE_API_KEY")

    if not api_key:
        print("\n" + "="*60)
        print("YOUTUBE API KEY REQUIRED")
        print("="*60)
        print("""
To fetch videos from YouTube channels, you need a free API key.

How to get one (takes 2 minutes):
1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Search for "YouTube Data API v3" and enable it
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. Copy the key

Then either:
  - Set environment variable: export YOUTUBE_API_KEY=your_key_here
  - Or paste it below when prompted
""")
        api_key = input("Paste your YouTube API key: ").strip()

        if not api_key:
            print("No API key provided. Exiting.")
            sys.exit(1)

    return api_key


def get_channel_id(youtube, handle: str) -> Optional[str]:
    """Convert a channel handle (@handle) to channel ID."""
    try:
        # Search for the channel by handle
        request = youtube.search().list(
            part="snippet",
            q=f"@{handle}",
            type="channel",
            maxResults=1
        )
        response = request.execute()

        if response.get("items"):
            return response["items"][0]["snippet"]["channelId"]
        return None
    except Exception as e:
        print(f"  ⚠ Error getting channel ID for @{handle}: {e}")
        return None


def get_uploads_playlist_id(youtube, channel_id: str) -> Optional[str]:
    """Get the uploads playlist ID for a channel."""
    try:
        request = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = request.execute()

        if response.get("items"):
            return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return None
    except Exception as e:
        print(f"  ⚠ Error getting uploads playlist: {e}")
        return None


def get_recent_videos(youtube, playlist_id: str, days_back: int, max_results: int = 10) -> list:
    """Get recent videos from a playlist (uploads)."""
    cutoff_date = datetime.now() - timedelta(days=days_back)
    videos = []

    try:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=min(max_results * 2, 50)  # Fetch extra to filter
        )
        response = request.execute()

        for item in response.get("items", []):
            snippet = item["snippet"]
            video_id = snippet["resourceId"]["videoId"]
            title = snippet["title"]
            published_at = snippet.get("publishedAt", "")
            description = snippet.get("description", "")

            # Parse date
            try:
                pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                pub_date = pub_date.replace(tzinfo=None)  # Make naive for comparison
            except:
                continue

            # Filter by date
            if pub_date < cutoff_date:
                continue

            # Skip shorts (usually have #shorts in title or description)
            if "#shorts" in title.lower() or "#shorts" in description.lower():
                continue
            if "/shorts/" in description:
                continue

            # Skip very short titles (likely shorts)
            if len(title) < 10:
                continue

            videos.append({
                "video_id": video_id,
                "title": title,
                "published_at": published_at,
                "description": description[:500],  # Truncate description
                "url": f"https://www.youtube.com/watch?v={video_id}"
            })

            if len(videos) >= max_results:
                break

        return videos

    except Exception as e:
        print(f"  ⚠ Error fetching videos: {e}")
        return []


# =============================================================================
# TRANSCRIPT FUNCTIONS
# =============================================================================

def get_transcript(video_id: str) -> Optional[str]:
    """Fetch transcript for a video."""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)

        # Combine all snippets into plain text
        text = " ".join([snippet.text for snippet in transcript.snippets])

        # Clean up common artifacts
        text = re.sub(r'\[Music\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[Applause\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    except Exception as e:
        error_name = type(e).__name__
        if "NoTranscript" in error_name or "TranscriptsDisabled" in error_name:
            return None
        print(f"    ⚠ Transcript error: {error_name}")
        return None


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def fetch_all_podcasts(api_key: str, days_back: int = 7, max_per_channel: int = 5) -> list:
    """Fetch recent videos and transcripts from all channels."""

    youtube = build("youtube", "v3", developerKey=api_key)
    all_episodes = []

    print(f"\nFetching episodes from {len(CHANNELS)} channels (last {days_back} days)...\n")

    for channel in CHANNELS:
        name = channel["name"]
        print(f"📺 {name}...")

        # Get channel ID
        if "channel_id" in channel:
            channel_id = channel["channel_id"]
        else:
            channel_id = get_channel_id(youtube, channel["handle"])

        if not channel_id:
            print(f"  ⚠ Could not find channel")
            continue

        # Get uploads playlist
        playlist_id = get_uploads_playlist_id(youtube, channel_id)
        if not playlist_id:
            print(f"  ⚠ Could not find uploads playlist")
            continue

        # Get recent videos
        videos = get_recent_videos(youtube, playlist_id, days_back, max_per_channel)

        if not videos:
            print(f"  (no new episodes)")
            continue

        # Fetch transcripts
        for video in videos:
            print(f"  ✓ {video['title'][:50]}...")

            transcript = get_transcript(video["video_id"])

            if transcript:
                print(f"    ✓ Got transcript ({len(transcript):,} chars)")
                all_episodes.append({
                    "podcast": name,
                    "title": video["title"],
                    "video_id": video["video_id"],
                    "url": video["url"],
                    "published_at": video["published_at"],
                    "description": video["description"],
                    "transcript": transcript,
                    "has_transcript": True
                })
            else:
                print(f"    ⚠ No transcript available")
                all_episodes.append({
                    "podcast": name,
                    "title": video["title"],
                    "video_id": video["video_id"],
                    "url": video["url"],
                    "published_at": video["published_at"],
                    "description": video["description"],
                    "transcript": None,
                    "has_transcript": False
                })

    return all_episodes


def main():
    parser = argparse.ArgumentParser(
        description="Fetch podcast transcripts from YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python fetch_podcasts.py                      # Default: 7 days, 5 per channel
    python fetch_podcasts.py --days 14            # Last 14 days
    python fetch_podcasts.py --max-per-channel 2  # Only 2 videos per channel
    python fetch_podcasts.py -o episodes.json     # Save to file

After running, share the JSON output with Claude to generate the magazine.
        """
    )
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--max-per-channel", type=int, default=5, help="Max videos per channel (default: 5)")
    parser.add_argument("-o", "--output", type=str, help="Output file (default: print to stdout)")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")

    args = parser.parse_args()

    # Get API key
    api_key = get_api_key()

    # Fetch episodes
    episodes = fetch_all_podcasts(
        api_key=api_key,
        days_back=args.days,
        max_per_channel=args.max_per_channel
    )

    # Summary
    total = len(episodes)
    with_transcript = sum(1 for e in episodes if e.get("has_transcript"))
    podcasts = len(set(e["podcast"] for e in episodes))

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total episodes found: {total}")
    print(f"With transcripts: {with_transcript}")
    print(f"Podcasts covered: {podcasts}")

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(episodes, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to: {args.output}")
        print(f"\nNext step: Share {args.output} with Claude to generate the magazine!")
    else:
        print(f"\n{'='*60}")
        print("JSON OUTPUT (copy everything below this line):")
        print("="*60 + "\n")
        print(json.dumps(episodes, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
