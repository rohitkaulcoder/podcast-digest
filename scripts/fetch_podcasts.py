#!/usr/bin/env python3
"""
Podcast Transcript Fetcher (v2)
===============================
Fetches transcripts from podcast RSS feeds using a tiered approach:
  Tier 1: RSS <podcast:transcript> tags (free)
  Tier 2: Groq Whisper on podcast audio (~$0.02/hr)
  Tier 3: YouTube transcript API (fallback, unreliable)

Usage:
    python fetch_podcasts.py                    # Fetch last 1 day
    python fetch_podcasts.py --days 7           # Fetch last 7 days
    python fetch_podcasts.py --max-per-channel 3
    python fetch_podcasts.py -o podcasts.json

Requirements:
    pip install feedparser groq google-api-python-client youtube-transcript-api
"""

import argparse
import json
import os
import re
import ssl
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from typing import Optional
from xml.etree import ElementTree

import feedparser

# =============================================================================
# CONFIGURATION - Podcasts with transcript source info
# =============================================================================

CHANNELS = [
    # --- Tier 1: RSS transcripts available ---
    {
        "name": "Cheeky Pint",
        "rss_url": "https://feeds.transistor.fm/cheeky-pint-with-john-collison",
        "has_rss_transcript": True,
        "handle": "stripe",
    },
    {
        "name": "Dwarkesh Podcast",
        "rss_url": "https://apple.dwarkesh-podcast.workers.dev/feed.rss",
        "has_rss_transcript": True,
        "handle": "DwarkeshPatel",
    },
    {
        "name": "Invest Like the Best",
        "rss_url": "https://feeds.megaphone.fm/CLS2859450455",
        "has_rss_transcript": True,
        "handle": "JoinColossus",
    },
    {
        "name": "Lenny's Podcast",
        "rss_url": "https://api.substack.com/feed/podcast/10845.rss",
        "has_rss_transcript": True,
        "handle": "lennyspodcast",
    },
    {
        "name": "The Knowledge Project",
        "rss_url": "https://feeds.megaphone.fm/FSMI7575968096",
        "has_rss_transcript": True,
        "handle": "tkppodcast",
    },
    {
        "name": "The Peel",
        "rss_url": "https://anchor.fm/s/e231a4ec/podcast/rss",
        "has_rss_transcript": True,
        "handle": "ThePeelPod",
    },
    # --- Tier 2: Groq Whisper (no RSS transcript) ---
    {
        "name": "Dialectic",
        "rss_url": "https://feeds.megaphone.fm/ICDEI1431648742",
        "has_rss_transcript": False,
        "handle": "Dialectic",
    },
    {
        "name": "20VC",
        "rss_url": "https://rss.libsyn.com/shows/61840/destinations/240976.xml",
        "has_rss_transcript": False,
        "handle": "20vc",
    },
    {
        "name": "Uncapped",
        "rss_url": "https://feeds.megaphone.fm/PDP4191604852",
        "has_rss_transcript": False,
        "handle": "uncappedpod",
    },
    {
        "name": "Founders",
        "rss_url": "https://feeds.megaphone.fm/DSLLC6297708582",
        "has_rss_transcript": False,
        "handle": "founderspodcast1",
    },
    {
        "name": "The A16Z Show",
        "rss_url": "https://feeds.simplecast.com/JGE3yC0V",
        "has_rss_transcript": False,
        "handle": "a16z",
    },
    {
        "name": "BG2",
        "rss_url": "https://anchor.fm/s/f06c2370/podcast/rss",
        "has_rss_transcript": False,
        "handle": "Bg2Pod",
    },
    {
        "name": "In Depth",
        "rss_url": "https://feeds.megaphone.fm/FRCH6787238462",
        "has_rss_transcript": False,
        "handle": "FirstRoundCapital",
    },
    {
        "name": "Y Combinator",
        "rss_url": "https://anchor.fm/s/8c1524bc/podcast/rss",
        "has_rss_transcript": False,
        "handle": "ycombinator",
    },
    {
        "name": "The Generalist",
        "rss_url": "https://feeds.transistor.fm/thegeneralistspodcast",
        "has_rss_transcript": False,
        "handle": "TheGeneralistPodcast",
    },
    {
        "name": "The Full Ratchet",
        "rss_url": "https://rss.libsyn.com/shows/55312/destinations/204448.xml",
        "has_rss_transcript": False,
        "handle": "fullratchet",
    },
]


# =============================================================================
# TIER 1: RSS TRANSCRIPT FETCHING
# =============================================================================

PODCAST_NS = "https://podcastindex.org/namespace/1.0"


def get_rss_episodes(rss_url: str, days_back: int, max_results: int) -> list:
    """Parse RSS feed and return recent episodes with metadata."""
    feed = feedparser.parse(rss_url)
    cutoff = datetime.now() - timedelta(days=days_back)
    episodes = []

    for entry in feed.entries:
        # Parse publication date
        pub_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            pub_date = datetime(*entry.updated_parsed[:6])

        if not pub_date or pub_date < cutoff:
            continue

        # Get audio enclosure URL
        audio_url = None
        for link in getattr(entry, "links", []):
            if link.get("type", "").startswith("audio/") or link.get("rel") == "enclosure":
                audio_url = link.get("href")
                break
        if not audio_url and hasattr(entry, "enclosures"):
            for enc in entry.enclosures:
                audio_url = enc.get("href")
                break

        episodes.append({
            "title": entry.get("title", ""),
            "published_at": pub_date.isoformat(),
            "description": entry.get("summary", "")[:500],
            "url": entry.get("link", ""),
            "audio_url": audio_url,
            "rss_entry": entry,  # keep for transcript extraction
        })

        if len(episodes) >= max_results:
            break

    return episodes


def extract_rss_transcript(entry) -> Optional[str]:
    """Extract transcript from RSS entry's <podcast:transcript> tag."""
    # feedparser may expose it as podcast_transcript or in the raw XML
    # Try multiple approaches

    # Approach 1: Check for podcast:transcript in links
    for link in getattr(entry, "links", []):
        link_type = link.get("type", "").lower()
        rel = link.get("rel", "").lower()
        if "transcript" in rel or link_type in (
            "application/srt",
            "application/x-subrip",
            "text/vtt",
            "text/plain",
            "text/html",
            "application/json",
        ):
            transcript_url = link.get("href")
            if transcript_url:
                return fetch_transcript_url(transcript_url, link_type)

    # Approach 2: Check for podcast_transcript attribute
    if hasattr(entry, "podcast_transcript"):
        t = entry.podcast_transcript
        url = t.get("url") if isinstance(t, dict) else getattr(t, "url", None)
        if url:
            type_ = t.get("type", "") if isinstance(t, dict) else getattr(t, "type", "")
            return fetch_transcript_url(url, type_)

    # Approach 3: Re-fetch the RSS and parse XML directly for this entry
    return None


def fetch_transcript_url(url: str, content_type: str) -> Optional[str]:
    """Fetch and parse a transcript URL (SRT, VTT, or plain text)."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "PodcastDigest/2.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")

        # Reject HTML pages (false positive transcript links)
        if raw.strip().startswith("<!DOCTYPE") or raw.strip().startswith("<html"):
            return None

        # Parse based on content type
        if "srt" in content_type or url.endswith(".srt"):
            return parse_srt(raw)
        elif "vtt" in content_type or url.endswith(".vtt"):
            return parse_vtt(raw)
        elif "json" in content_type or url.endswith(".json"):
            return parse_json_transcript(raw)
        else:
            # Assume plain text, clean it up
            text = re.sub(r"\s+", " ", raw).strip()
            return text if len(text) > 100 else None

    except Exception as e:
        print(f"    ⚠ Error fetching transcript URL: {e}")
        return None


def parse_srt(raw: str) -> str:
    """Parse SRT subtitle format to plain text."""
    lines = []
    for line in raw.split("\n"):
        line = line.strip()
        # Skip sequence numbers, timestamps, and blank lines
        if not line or re.match(r"^\d+$", line) or re.match(r"\d{2}:\d{2}:", line):
            continue
        lines.append(line)
    return " ".join(lines)


def parse_vtt(raw: str) -> str:
    """Parse WebVTT format to plain text."""
    lines = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if re.match(r"\d{2}:\d{2}:", line) or "-->" in line:
            continue
        # Remove VTT tags like <v Speaker>
        line = re.sub(r"<[^>]+>", "", line)
        lines.append(line)
    # Deduplicate consecutive identical lines (common in VTT)
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    return " ".join(deduped)


def parse_json_transcript(raw: str) -> str:
    """Parse JSON transcript format to plain text."""
    try:
        data = json.loads(raw)
        # Common formats: list of segments with "text" or "body" fields
        if isinstance(data, list):
            texts = [seg.get("text") or seg.get("body", "") for seg in data]
            return " ".join(t for t in texts if t)
        elif isinstance(data, dict) and "segments" in data:
            texts = [seg.get("text", "") for seg in data["segments"]]
            return " ".join(t for t in texts if t)
    except:
        pass
    return None


# =============================================================================
# TIER 1.5: RSS RAW XML TRANSCRIPT CHECK
# =============================================================================

def check_rss_transcript_xml(rss_url: str, episode_title: str) -> Optional[str]:
    """Re-fetch RSS XML and look for <podcast:transcript> tags directly."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(rss_url, headers={"User-Agent": "PodcastDigest/2.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            raw_xml = resp.read()

        root = ElementTree.fromstring(raw_xml)

        for item in root.iter("item"):
            title_el = item.find("title")
            if title_el is None:
                continue
            item_title = title_el.text or ""

            # Fuzzy match on title
            if episode_title.lower()[:40] not in item_title.lower() and item_title.lower()[:40] not in episode_title.lower():
                continue

            # Look for podcast:transcript element
            for child in item:
                tag = child.tag.lower()
                if "transcript" in tag:
                    url = child.get("url")
                    type_ = child.get("type", "")
                    if url:
                        return fetch_transcript_url(url, type_)

    except Exception as e:
        print(f"    ⚠ XML transcript check error: {e}")

    return None


# =============================================================================
# TIER 2: GROQ WHISPER TRANSCRIPTION
# =============================================================================

def transcribe_with_groq(audio_url: str) -> Optional[str]:
    """Download podcast audio and transcribe with Groq Whisper."""
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        print("    ⚠ GROQ_API_KEY not set, skipping Whisper transcription")
        return None

    try:
        from groq import Groq
    except ImportError:
        print("    ⚠ groq package not installed (pip install groq)")
        return None

    try:
        # Download audio to temp file
        print(f"    ⬇ Downloading audio...")
        ctx = ssl.create_default_context()
        req = urllib.request.Request(audio_url, headers={"User-Agent": "PodcastDigest/2.0"})
        with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
            suffix = ".mp3"
            if "mp4" in audio_url or "m4a" in audio_url:
                suffix = ".m4a"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(resp.read())
                tmp_path = tmp.name

        # Check file size — Groq has a 25MB limit, compress if needed
        file_size = os.path.getsize(tmp_path)
        if file_size > 24 * 1024 * 1024:
            print(f"    🔧 Compressing audio ({file_size // 1024 // 1024}MB → mono 16kHz)...")
            compressed_path = tmp_path + ".compressed.mp3"
            ret = os.system(
                f'ffmpeg -y -i "{tmp_path}" -ac 1 -ar 16000 -b:a 32k "{compressed_path}" -loglevel error 2>&1'
            )
            os.unlink(tmp_path)
            if ret != 0 or not os.path.exists(compressed_path):
                print(f"    ⚠ ffmpeg compression failed")
                return None
            tmp_path = compressed_path
            file_size = os.path.getsize(tmp_path)
            print(f"    ✓ Compressed to {file_size // 1024 // 1024}MB")

            if file_size > 25 * 1024 * 1024:
                print(f"    ⚠ Still too large after compression ({file_size // 1024 // 1024}MB)")
                os.unlink(tmp_path)
                return None

        print(f"    🎙 Transcribing with Groq Whisper ({file_size // 1024 // 1024}MB)...")
        client = Groq(api_key=groq_key)

        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(tmp_path), audio_file),
                model="whisper-large-v3-turbo",
                response_format="text",
            )

        os.unlink(tmp_path)

        text = str(transcription).strip()
        if len(text) > 100:
            return text
        return None

    except Exception as e:
        print(f"    ⚠ Groq transcription error: {e}")
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass
        return None


# =============================================================================
# TIER 3: YOUTUBE TRANSCRIPT (FALLBACK)
# =============================================================================

def get_youtube_transcript(handle: str, episode_title: str) -> Optional[str]:
    """Try to get transcript from YouTube as last resort."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from googleapiclient.discovery import build

        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            return None

        youtube = build("youtube", "v3", developerKey=api_key)

        # Search for the episode on the channel
        request = youtube.search().list(
            part="snippet",
            q=f"@{handle} {episode_title}",
            type="video",
            maxResults=1,
        )
        response = request.execute()

        if not response.get("items"):
            return None

        video_id = response["items"][0]["id"]["videoId"]
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        text = " ".join([s.text for s in transcript.snippets])
        text = re.sub(r"\[Music\]", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\[Applause\]", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    except Exception as e:
        return None


# =============================================================================
# TIERED TRANSCRIPT ORCHESTRATOR
# =============================================================================

def get_transcript_tiered(channel: dict, episode: dict) -> tuple[Optional[str], str]:
    """
    Try to get transcript using tiered approach.
    Returns (transcript_text, source) where source is 'rss', 'groq_whisper', 'youtube', or 'none'.
    """
    title = episode["title"]

    # Tier 1: RSS transcript
    if channel.get("has_rss_transcript"):
        rss_entry = episode.get("rss_entry")
        if rss_entry:
            transcript = extract_rss_transcript(rss_entry)
            if transcript and len(transcript) > 100:
                return transcript, "rss"

        # Tier 1.5: Try raw XML parsing
        transcript = check_rss_transcript_xml(channel["rss_url"], title)
        if transcript and len(transcript) > 100:
            return transcript, "rss"

    # Tier 2: Groq Whisper
    audio_url = episode.get("audio_url")
    if audio_url:
        transcript = transcribe_with_groq(audio_url)
        if transcript:
            return transcript, "groq_whisper"

    # Tier 3: YouTube fallback
    handle = channel.get("handle")
    if handle:
        print(f"    🔄 Trying YouTube fallback...")
        transcript = get_youtube_transcript(handle, title)
        if transcript:
            return transcript, "youtube"

    return None, "none"


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def fetch_all_podcasts(days_back: int = 1, max_per_channel: int = 5) -> list:
    """Fetch recent episodes and transcripts from all channels."""
    all_episodes = []

    print(f"\nFetching episodes from {len(CHANNELS)} channels (last {days_back} days)...\n")

    for channel in CHANNELS:
        name = channel["name"]
        rss_url = channel["rss_url"]
        print(f"🎙 {name}...")

        # Discover episodes from RSS feed
        episodes = get_rss_episodes(rss_url, days_back, max_per_channel)

        if not episodes:
            print(f"  (no new episodes)")
            continue

        # Fetch transcripts for each episode
        for ep in episodes:
            print(f"  ✓ {ep['title'][:60]}...")

            transcript, source = get_transcript_tiered(channel, ep)

            if transcript:
                print(f"    ✓ Got transcript via {source} ({len(transcript):,} chars)")
            else:
                print(f"    ⚠ No transcript available")

            all_episodes.append({
                "podcast": name,
                "title": ep["title"],
                "url": ep["url"],
                "published_at": ep["published_at"],
                "description": ep["description"],
                "transcript": transcript,
                "transcript_length": len(transcript) if transcript else 0,
                "has_transcript": transcript is not None,
                "transcript_source": source,
            })

    return all_episodes


def main():
    parser = argparse.ArgumentParser(
        description="Fetch podcast transcripts (RSS → Groq Whisper → YouTube fallback)",
    )
    parser.add_argument("--days", type=int, default=1, help="Days to look back (default: 1)")
    parser.add_argument("--max-per-channel", type=int, default=5, help="Max episodes per channel (default: 5)")
    parser.add_argument("-o", "--output", type=str, help="Output file (default: print to stdout)")

    args = parser.parse_args()

    episodes = fetch_all_podcasts(
        days_back=args.days,
        max_per_channel=args.max_per_channel,
    )

    # Summary
    total = len(episodes)
    with_transcript = sum(1 for e in episodes if e["has_transcript"])
    by_source = {}
    for e in episodes:
        src = e["transcript_source"]
        by_source[src] = by_source.get(src, 0) + 1

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total episodes found: {total}")
    print(f"With transcripts: {with_transcript}")
    print(f"By source: {json.dumps(by_source)}")

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(episodes, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to: {args.output}")
    else:
        print(json.dumps(episodes, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
