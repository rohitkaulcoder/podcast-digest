# Podcast Digest

Daily insights from the best podcasts, distilled into digestible highlights.

## What is this?

An automated podcast digest system that fetches transcripts from YouTube podcast channels, generates highlight-driven HTML digests using Claude Code, and publishes to GitHub Pages. Also pushes highlights to Readwise.

## How it works

**Local automation via macOS launchd (3-stage pipeline):**

1. **Fetch** — Pulls transcripts from YouTube podcast channels
2. **Generate** — Claude Code analyzes transcripts and creates an HTML digest with categorized insights
3. **Publish** — Commits and pushes to GitHub Pages

Plus a daily health check with macOS notifications.

**Also has a GitHub Actions workflow** (`fetch-podcasts.yml`) for cloud-based fetch + chunk preparation.

### Cost

- Claude Code for analysis (uses Max plan — no API costs)
- YouTube API free tier
- GitHub Pages free hosting

## Browse Digests

Visit the live archive: **https://rohitkaulcoder.github.io/podcast-digest/**

## Insight Categories

Each deep dive episode is analyzed for:

| Category | Description |
|----------|-------------|
| 🎯 **Core Insights** | Central thesis, main arguments, foundational ideas |
| 🔄 **Counter-Intuitive** | Challenges conventional wisdom, surprising reversals |
| 📊 **Data Points** | Specific numbers, benchmarks, statistics |
| 🔮 **Future-Looking** | Predictions, emerging trends, what's coming |

## Monitored Podcasts

23 channels including:
- Acquired / ACQ2
- BG²
- Dwarkesh Podcast
- Lenny's Podcast
- No Priors
- 20VC
- Y Combinator
- And 16 more...

## Tech Stack

- **Automation**: macOS launchd (local) + GitHub Actions (cloud backup)
- **Data fetching**: YouTube Transcript API + YouTube Data API v3
- **Analysis**: Claude Code (non-interactive mode)
- **Highlights**: Pushed to Readwise via `push_to_readwise.py`
- **Hosting**: GitHub Pages
- **Notifications**: macOS notification system
- **Monitoring**: Daily health checks

## Setup

See [SETUP.md](SETUP.md) for complete installation instructions.

Quick start:
```bash
~/setup_3step_automation.sh
```

## Monitoring

**Daily notifications:**
- ✅ Success: "Podcast Fetch Complete", "Digest Generated", "Published to GitHub"
- ❌ Errors: "FAILED" notifications with log details
- 🏥 Health: Daily health report at 9 AM

**Check status:**
```bash
~/podcast_health_check.sh
```

**View logs:**
```bash
tail -f ~/podcast_step1_fetch.log      # Fetch (5:00 PM)
tail -f ~/podcast_step2_generate.log   # Generate (5:15 PM)
tail -f ~/podcast_step3_publish.log    # Publish (5:30 PM)
tail -f ~/podcast_health_check.log     # Health (9:00 AM)
```

## Architecture

```
┌─────────────────────────────────────────────┐
│  macOS launchd Jobs (Automated)             │
└─────────────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  5:00 PM - Fetch Transcripts  │
    │  → podcasts.json              │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  5:15 PM - Generate Digest    │
    │  → digest_YYYY-MM-DD.html     │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  5:30 PM - Publish to GitHub  │
    │  → GitHub Pages               │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  9:00 AM - Health Check       │
    │  → macOS notification         │
    └───────────────────────────────┘
```

## Repository Structure

```
podcast-digest/
├── .github/workflows/
│   └── fetch-podcasts.yml        # GitHub Actions fetch workflow
├── scripts/
│   ├── fetch_podcasts.py         # YouTube transcript fetcher
│   ├── generate_digest_html.py   # HTML digest generator
│   ├── prepare_digest_chunks.py  # Chunk prep for analysis
│   └── push_to_readwise.py      # Push highlights to Readwise
├── data/chunks/                  # Episode chunk data
├── digest_*.html                 # Generated digests
├── index.html                    # Archive landing page
├── README.md
└── SETUP.md
```

Last updated: April 2026
