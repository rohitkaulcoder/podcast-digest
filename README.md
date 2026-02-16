# 🎙️ Podcast Digest

Daily insights from the best podcasts, distilled into digestible nuggets.

## What is this?

An automated podcast digest system that fetches, analyzes, and publishes podcast insights daily. Each digest contains:

- **Deep Dives**: Full-length episodes with 8-12 categorized insights
- **Quick Hits**: Shorter clips with 1-2 key takeaways

## How it works

**Fully automated via local launchd jobs:**

1. **Daily fetch (5:00 PM)**: Fetches transcripts from 23 YouTube podcast channels
2. **Generate digest (5:15 PM)**: Claude Code analyzes transcripts and creates HTML digest
3. **Auto-publish (5:30 PM)**: Commits and pushes to GitHub Pages
4. **Health check (9:00 AM)**: Daily monitoring with notifications

### 🚀 Completely Automated & FREE

- Uses macOS launchd (runs even when laptop was asleep!)
- Claude Code for analysis (no API costs)
- GitHub Pages for hosting
- macOS notifications for status updates

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

- **Automation**: macOS launchd (4 separate jobs)
- **Data fetching**: YouTube Transcript API + YouTube Data API v3
- **Analysis**: Claude Code (non-interactive mode)
- **Hosting**: GitHub Pages
- **Notifications**: macOS notification system
- **Monitoring**: Daily health checks

## Features

✅ **Automated Workflow**
- Fetches new episodes daily at 5 PM
- Generates insights automatically
- Publishes to web instantly
- Zero manual intervention

✅ **Reliable**
- launchd catches up if laptop was asleep
- Separate jobs for each step (better debugging)
- Error notifications via macOS
- Daily health check at 9 AM

✅ **Free**
- No API costs (uses Claude Code subscription)
- YouTube API free tier (10K quota/day)
- GitHub Pages free hosting
- $0/month total cost

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
├── .github/workflows/          # GitHub Actions (backup)
├── scripts/
│   ├── fetch_podcasts.py       # YouTube transcript fetcher
│   └── prepare_digest_chunks.py
├── data/                       # Episode data
├── digest_*.html               # Generated digests
├── index.html                  # Archive landing page
├── README.md                   # This file
└── SETUP.md                    # Setup instructions
```

## Contributing

This is a personal project, but feel free to fork and adapt for your own podcast subscriptions!

---

**Generated with 💙 by [Claude](https://claude.ai)**

Last updated: February 2026
