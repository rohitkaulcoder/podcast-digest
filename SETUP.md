# 🚀 Podcast Digest - Complete Setup Guide

Fully automated local setup using macOS launchd + Claude Code (NO API COSTS!)

## 📋 Prerequisites

- macOS (uses launchd for scheduling)
- Claude Code installed
- Python 3.x
- YouTube Data API key (free)
- GitHub repository access
- Git configured

---

## 🔧 Quick Setup

Run the automated setup script:

```bash
~/setup_3step_automation.sh
```

This will:
- ✅ Verify all prerequisites
- ✅ Load 4 launchd jobs (fetch, generate, publish, health-check)
- ✅ Set up notifications
- ✅ Configure monitoring

---

## 📝 Manual Setup (If Needed)

### 1. Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "YouTube Data API v3"
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy the API key

### 2. Configure Scripts

The API key is already set in:
- `~/auto_fetch_podcasts.sh`
- `~/.github/workflows/fetch-podcasts.yml` (for backup)

### 3. Load launchd Jobs

```bash
# Load all 4 jobs
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-step1-fetch.plist
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-step2-generate.plist
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-step3-publish.plist
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-health-check.plist
```

### 4. Verify Setup

```bash
# Check all jobs are loaded
launchctl list | grep podcast

# Should show 4 jobs:
# - com.rohitkaul.podcast-step1-fetch
# - com.rohitkaul.podcast-step2-generate
# - com.rohitkaul.podcast-step3-publish
# - com.rohitkaul.podcast-health-check
```

---

## 📅 Automation Schedule

### Daily at 5:00 PM
**Step 1: Fetch Transcripts**
- Script: `~/auto_fetch_podcasts.sh`
- Fetches episodes from last 1 day
- Monitors 23 YouTube podcast channels
- Output: `~/podcasts.json`
- Log: `~/podcast_step1_fetch.log`
- Notification: "Podcast Fetch Complete - Found X episodes"

### Daily at 5:15 PM
**Step 2: Generate Digest**
- Script: `~/auto_generate_digest.sh`
- Uses Claude Code in non-interactive mode (`--print --dangerously-skip-permissions`)
- Analyzes transcripts and extracts insights
- Output: `~/Projects/podcast-digest/digest_YYYY-MM-DD.html`
- Updates: `index.html`
- Log: `~/podcast_step2_generate.log`
- Notification: "Digest Generated - Created digest for DATE"

### Daily at 5:30 PM
**Step 3: Publish to GitHub**
- Script: `~/auto_publish_to_github.sh`
- Commits digest files
- Pushes to GitHub (auto-publishes to GitHub Pages)
- Log: `~/podcast_step3_publish.log`
- Notification: "Published to GitHub - Digest is now live!"

### Daily at 9:00 AM
**Health Check**
- Script: `~/podcast_health_check.sh`
- Verifies all jobs are loaded
- Checks for recent digests
- Scans logs for errors
- Tests GitHub connectivity
- Log: `~/podcast_health_check.log`
- Notification: "Podcast Automation - Healthy" or "Issues Detected"

---

## 🔔 Notification System

All steps send macOS notifications:

**Success Notifications (Glass sound):**
- ✅ "Podcast Fetch Complete"
- ✅ "Digest Generated"
- ✅ "Published to GitHub"
- ✅ "Podcast Automation - Healthy"

**Error Notifications (Basso sound):**
- ❌ "Podcast Fetch FAILED"
- ❌ "Digest Generation FAILED"
- ❌ "GitHub Push FAILED"
- ❌ "Podcast Automation - Issues Detected"

Test notifications:
```bash
~/send_notification.sh "Test Title" "Test Message" "success"
~/send_notification.sh "Error Test" "Test Error" "error"
```

---

## 📊 Monitoring & Logs

### View Logs (Real-time)

```bash
# Step 1: Fetch
tail -f ~/podcast_step1_fetch.log

# Step 2: Generate
tail -f ~/podcast_step2_generate.log

# Step 3: Publish
tail -f ~/podcast_step3_publish.log

# Health Check
tail -f ~/podcast_health_check.log
```

### Manual Health Check

```bash
~/podcast_health_check.sh
```

Shows:
- ✅ Active launchd jobs
- ✅ Recent digests
- ✅ Log errors
- ✅ GitHub connectivity
- ✅ Last successful runs

---

## 🛠️ Troubleshooting

### Jobs Not Running?

```bash
# Check if jobs are loaded
launchctl list | grep podcast

# If missing, load them
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-step*.plist
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-health-check.plist
```

### Test Jobs Manually (Don't Wait for 5 PM)

```bash
# Run each step individually
~/auto_fetch_podcasts.sh        # Step 1
~/auto_generate_digest.sh       # Step 2
~/auto_publish_to_github.sh     # Step 3
~/podcast_health_check.sh       # Health check
```

### Force Run via launchd

```bash
# Trigger immediately
launchctl start com.rohitkaul.podcast-step1-fetch
```

### View Recent Errors

```bash
# Last 20 lines of each log
tail -20 ~/podcast_step1_fetch.log
tail -20 ~/podcast_step2_generate.log
tail -20 ~/podcast_step3_publish.log
```

### Reload Jobs (After Editing)

```bash
# Unload
launchctl unload ~/Library/LaunchAgents/com.rohitkaul.podcast-step*.plist

# Reload
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-step1-fetch.plist
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-step2-generate.plist
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-step3-publish.plist
```

---

## 🎯 How launchd Works

### Key Advantage: Catches Up When Laptop Wakes

**Scenario 1: Laptop is on at 5 PM**
- ✅ All jobs run on schedule

**Scenario 2: Laptop is asleep at 5 PM**
- Laptop wakes at 6:30 PM
- ✅ launchd sees "I missed the 5 PM job"
- ✅ Runs all 3 jobs immediately in sequence

**Scenario 3: Laptop turned off all day**
- Jobs won't run until next day
- ✅ Resume normal schedule next day at 5 PM

---

## 🎨 Customization

### Change Schedule Time

Edit the `.plist` files in `~/Library/LaunchAgents/`:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>17</integer>  <!-- 5 PM, change to 18 for 6 PM -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

Then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.rohitkaul.podcast-step1-fetch.plist
launchctl load ~/Library/LaunchAgents/com.rohitkaul.podcast-step1-fetch.plist
```

### Add More Podcast Channels

Edit `~/Projects/podcast-digest/scripts/fetch_podcasts.py`:

```python
CHANNELS = [
    # ... existing channels ...
    {"name": "New Podcast", "handle": "youtube_handle"},
]
```

Or use `channel_id` if handle doesn't work:
```python
{"name": "New Podcast", "channel_id": "UCxxxxxxxxxxxxx"},
```

### Fetch More Days of History

Edit `~/auto_fetch_podcasts.sh`:

```bash
# Change from --days 1 to --days 7
python3 fetch_podcasts.py --days 7 --max-per-channel 5 -o podcasts.json
```

---

## 💰 Cost Breakdown

| Component | Cost |
|-----------|------|
| Claude Code subscription | Already paying |
| YouTube Data API | Free (10K quota/day) |
| GitHub Pages | Free |
| macOS launchd | Free |
| **Total** | **$0/month** |

---

## 📁 File Structure

### Scripts (~/):
```
~/auto_fetch_podcasts.sh           # Step 1: Fetch
~/auto_generate_digest.sh          # Step 2: Generate
~/auto_publish_to_github.sh        # Step 3: Publish
~/podcast_health_check.sh          # Health monitoring
~/send_notification.sh             # Notification helper
~/setup_3step_automation.sh        # Easy setup
```

### launchd Jobs (~/Library/LaunchAgents/):
```
com.rohitkaul.podcast-step1-fetch.plist
com.rohitkaul.podcast-step2-generate.plist
com.rohitkaul.podcast-step3-publish.plist
com.rohitkaul.podcast-health-check.plist
```

### Logs (~/):
```
~/podcast_step1_fetch.log
~/podcast_step2_generate.log
~/podcast_step3_publish.log
~/podcast_health_check.log
~/podcast_fetch.log (legacy)
```

### Repository (~/Projects/podcast-digest/):
```
digest_YYYY-MM-DD.html    # Generated digests
index.html                # Archive page
data/                     # Episode data
scripts/                  # Python scripts
```

---

## 🔒 Security Notes

- API keys are in local scripts (not in git)
- Uses `--dangerously-skip-permissions` for Claude Code automation
  - Safe because it only runs trusted scripts you created
  - Only used in non-interactive automation context
- GitHub credentials use system git config

---

## ✅ Success Checklist

- [ ] YouTube API key configured
- [ ] All 4 launchd jobs loaded
- [ ] Received test notification
- [ ] Health check passes
- [ ] GitHub repository accessible
- [ ] First digest generated successfully
- [ ] Published to GitHub Pages

---

## 📚 Additional Documentation

- `~/AUTOMATION_GUIDE.md` - Complete automation details
- `~/MONITORING_GUIDE.md` - Monitoring & troubleshooting
- This file - Setup instructions

---

## 🆘 Support

**Check logs first:**
```bash
tail -50 ~/podcast_step*.log
```

**Run health check:**
```bash
~/podcast_health_check.sh
```

**Common issues:**
- **No episodes found**: Normal! Podcasts don't publish daily
- **GitHub push failed**: Check internet connection, git credentials
- **Claude Code error**: Verify Claude Code is installed and updated

---

🎉 **Setup Complete!** Your podcast digest will now run automatically every day at 5 PM, with notifications keeping you informed!

**Live site:** https://rohitkaulcoder.github.io/podcast-digest/

---

Last updated: February 2026
