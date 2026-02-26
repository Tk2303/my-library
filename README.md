# 🤖 GitHub Library Sync Agent

Automatically uploads every program in your local library to a GitHub repository — every day, without fail.

---

## What It Does

- Scans your local **programs folder** for code files
- **Creates or updates** files in your GitHub repo via the API
- Skips files that haven't changed (uses an MD5 cache for speed)
- Runs on a **daily schedule** via cron (Linux/macOS) or Task Scheduler (Windows)
- Writes a **log file** so you can verify every run

---

## Quick Start (3 steps)

### 1. Install dependencies

```bash
pip install requests
```

### 2. Configure the agent

```bash
python github_sync.py --setup
```

You'll be prompted for:

| Field | Description |
|---|---|
| GitHub Token | A Personal Access Token with **repo** scope — create one at https://github.com/settings/tokens |
| GitHub Username | Your GitHub username |
| Repository name | Target repo (will be **auto-created** if it doesn't exist) |
| Library path | Absolute path to your programs folder, e.g. `/home/you/projects` |
| Branch | Target branch (default: `main`) |

This saves a `config.json` file you can also edit directly.

### 3. Schedule daily runs

```bash
python install_scheduler.py
```

This adds a cron job (Linux/macOS) or Task Scheduler entry (Windows) to run the sync every day at **9:00 AM**.

---

## Manual Usage

```bash
# Preview what would be uploaded (no changes made)
python github_sync.py --dry-run

# Run a sync right now
python github_sync.py --run

# Reconfigure settings
python github_sync.py --setup
```

---

## Configuration (`config.json`)

```json
{
  "github_token": "ghp_...",
  "github_username": "your-username",
  "repo_name": "my-library",
  "library_path": "/home/you/projects",
  "branch": "main",
  "commit_message": "🤖 Auto-sync: {date}",
  "extensions": [".py", ".js", ".ts", ".java", "..."],
  "ignore_dirs": [".git", "__pycache__", "node_modules", "..."],
  "max_file_size_mb": 10,
  "dry_run": false
}
```

**To add or remove file types**, edit the `extensions` list.  
**To sync ALL file types**, set `extensions` to `[]`.

---

## Files

| File | Purpose |
|---|---|
| `github_sync.py` | Main agent script |
| `install_scheduler.py` | Sets up daily scheduling |
| `config.json` | Your settings (auto-created on first `--setup`) |
| `.sync_cache.json` | MD5 cache to skip unchanged files |
| `sync.log` | Log of every sync run |

---

## How to Get a GitHub Token

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Give it a name like `sync-agent`
4. Check the **`repo`** scope (full control of private repositories)
5. Click **Generate token** and copy the value
6. Paste it during `--setup`

---

## Changing the Schedule

Edit `install_scheduler.py` and change `HOUR` and `MINUTE` at the top, then re-run it.

**Linux/macOS** — you can also edit your crontab directly:
```bash
crontab -e
```
The entry looks like:
```
0 9 * * * /usr/bin/python3 /path/to/github_sync.py --run >> /path/to/sync.log 2>&1
```

**Windows** — open Task Scheduler and modify the `GitHubLibrarySyncAgent` task.

---

## Security Note

Your token is stored in `config.json` as plain text. Make sure to:
- Keep `config.json` out of any public repository (it's auto-ignored if you put `.sync_cache.json` and `config.json` in `.gitignore`)
- Use a token with the **minimum required scope** (just `repo`)
- Rotate the token if you suspect it's been exposed
