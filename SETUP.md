# 🚀 GitHub Actions Setup Guide

This guide will help you migrate from local cron jobs to GitHub Actions for fully automated, cloud-based podcast fetching.

## 📋 Prerequisites

- GitHub account
- YouTube Data API key (free)
- This repository pushed to GitHub

## 🔧 Setup Steps

### 1. Get Your YouTube API Key

If you don't already have one:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "YouTube Data API v3"
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy the API key

### 2. Add API Key to GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `YOUTUBE_API_KEY`
5. Value: Paste your YouTube API key
6. Click **Add secret**

### 3. Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. If prompted, enable GitHub Actions for this repository
3. You should see the "Fetch Podcasts Daily" workflow

### 4. Configure Schedule (Optional)

The workflow runs daily at **8:00 AM UTC** by default.

To change the schedule, edit `.github/workflows/fetch-podcasts.yml`:

```yaml
schedule:
  - cron: '0 8 * * *'  # Format: minute hour day month weekday
```

**Common schedules:**
- `0 8 * * *` - Daily at 8 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 12 * * 1` - Every Monday at noon
- `0 20 * * *` - Daily at 8 PM UTC

### 5. Test the Workflow

**Manual trigger (recommended for first run):**

1. Go to **Actions** tab
2. Select "Fetch Podcasts Daily" workflow
3. Click **Run workflow**
4. Choose number of days to fetch (default: 1)
5. Click **Run workflow**

Watch the workflow run in real-time! ✨

### 6. Verify Results

After the workflow completes:

1. Check the **Actions** tab for workflow status (green ✅ = success)
2. Go to the repository root - you should see a new commit
3. Check `data/podcasts.json` - it should contain fetched episodes
4. Check `data/chunks/` - processed chunks should be there

## 📁 Repository Structure

```
podcast-digest/
├── .github/
│   └── workflows/
│       └── fetch-podcasts.yml      # GitHub Actions workflow
├── scripts/
│   ├── fetch_podcasts.py           # Fetch transcripts from YouTube
│   └── prepare_digest_chunks.py    # Process into chunks
├── data/
│   ├── podcasts.json               # Raw fetched data
│   └── chunks/                     # Processed chunks
│       ├── _metadata.json
│       ├── episode_XX_full.json
│       └── quick_hits_all.json
├── digest_YYYY-MM-DD.html          # Generated digest pages
├── index.html                       # Archive landing page
├── requirements.txt                 # Python dependencies
└── README.md
```

## 🔍 Monitoring & Troubleshooting

### Check Workflow Status

- **Actions tab**: See all workflow runs
- **Email notifications**: GitHub sends emails on workflow failures
- **Commit history**: Each successful run creates a commit

### Common Issues

#### ❌ "YouTube API key not found"

**Solution:** Make sure you added `YOUTUBE_API_KEY` to GitHub Secrets (see Step 2)

#### ❌ "API quota exceeded"

**Cause:** YouTube API has a 10,000 units/day quota (plenty for normal use)

**Solution:**
- Wait until quota resets (midnight Pacific Time)
- Reduce `--max-per-channel` in workflow if fetching too many

#### ❌ "No changes to commit"

**Not an error!** This means no new episodes were found since last run.

#### ❌ "Script failed to run"

**Solution:**
1. Check the workflow logs in Actions tab
2. Verify Python scripts are in `scripts/` directory
3. Check that `requirements.txt` is present

### View Detailed Logs

1. Go to **Actions** tab
2. Click on a workflow run
3. Click on the job name
4. Expand any step to see detailed logs

## 🎯 Manual Triggers

You can manually trigger the workflow anytime:

```bash
# Via GitHub UI
Actions → Fetch Podcasts Daily → Run workflow

# Via GitHub CLI (if installed)
gh workflow run fetch-podcasts.yml -f days=7
```

## 📊 Resource Usage

### Free Tier Limits (more than sufficient!)

| Resource | Free Tier | Your Usage (est.) |
|----------|-----------|-------------------|
| **Actions minutes** | 2,000/month | ~60/month |
| **Storage** | 1GB | <10MB |
| **Bandwidth** | 1GB/month | <100MB/month |

### Cost Estimate

**$0/month** - Well within free tier limits ✅

## 🔄 Migrating from Local Cron

### Disable Local Automation

Once GitHub Actions is working:

```bash
# List current launchd jobs
launchctl list | grep podcast

# Unload the local automation
launchctl unload ~/Library/LaunchAgents/com.user.fetch-podcasts.plist

# Optional: Remove the plist file
rm ~/Library/LaunchAgents/com.user.fetch-podcasts.plist
```

### Benefits of GitHub Actions vs Local

| Feature | Local Cron | GitHub Actions |
|---------|-----------|----------------|
| **Reliability** | Only when Mac is on | 99.9% uptime |
| **Dependency** | Local machine | Cloud-based |
| **Logs** | Local file | Web UI + history |
| **Notifications** | None | Email on failure |
| **Version control** | Manual | Automatic |
| **Collaboration** | Difficult | Easy |
| **Cost** | Free | Free |

## 🎨 Customization

### Add More Channels

Edit `scripts/fetch_podcasts.py`:

```python
CHANNELS = [
    # ... existing channels ...
    {"name": "New Podcast", "handle": "youtube_handle"},
]
```

Commit and push - next run will include the new channel!

### Change Fetch Parameters

Edit `.github/workflows/fetch-podcasts.yml`:

```yaml
python3 scripts/fetch_podcasts.py --days 3 --max-per-channel 10 -o data/podcasts.json
```

### Add Email Notifications

Add this step to the workflow:

```yaml
- name: Send email on failure
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: Podcast fetch failed
    body: Check the workflow logs
    to: your-email@example.com
    from: GitHub Actions
```

## 🆘 Support

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Workflow Syntax**: https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions
- **YouTube API Docs**: https://developers.google.com/youtube/v3

## ✅ Success Checklist

- [ ] YouTube API key added to GitHub Secrets
- [ ] GitHub Actions enabled for repository
- [ ] First manual workflow run completed successfully
- [ ] `data/podcasts.json` contains episodes
- [ ] Scheduled workflow configured (daily at 8 AM)
- [ ] Local cron job disabled (optional)
- [ ] Email notifications configured (optional)

---

🎉 **Congratulations!** Your podcast digest is now fully automated in the cloud!
