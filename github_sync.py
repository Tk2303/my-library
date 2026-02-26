#!/usr/bin/env python3
"""
GitHub Library Sync Agent
Automatically uploads programs from your local library to GitHub daily.
"""

import os
import sys
import json
import base64
import hashlib
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional
import requests

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_FILE = Path(__file__).parent / "sync.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("github-sync")


# ── Config ─────────────────────────────────────────────────────────────────────
CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "github_token": "",          # Personal Access Token (repo scope)
    "github_username": "",       # Your GitHub username
    "repo_name": "",             # Target repository name
    "library_path": "",          # Absolute path to your programs folder
    "branch": "main",            # Target branch
    "commit_message": "🤖 Auto-sync: {date}",
    "extensions": [              # File extensions to upload (empty = all)
        ".py", ".js", ".ts", ".java", ".c", ".cpp",
        ".go", ".rs", ".rb", ".sh", ".html", ".css",
        ".md", ".json", ".yaml", ".yml", ".toml",
        ".r", ".sql", ".swift", ".kt", ".cs",
    ],
    "ignore_dirs": [             # Directories to skip
        ".git", "__pycache__", "node_modules", ".venv",
        "venv", "env", ".idea", ".vscode", "dist", "build",
    ],
    "max_file_size_mb": 10,      # Skip files larger than this
    "dry_run": False,            # Set True to preview without uploading
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            saved = json.load(f)
        cfg = {**DEFAULT_CONFIG, **saved}
        return cfg
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    log.info("Config saved to %s", CONFIG_FILE)


# ── GitHub API helpers ─────────────────────────────────────────────────────────
class GitHubAPI:
    BASE = "https://api.github.com"

    def __init__(self, token: str, username: str, repo: str, branch: str):
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.username = username
        self.repo = repo
        self.branch = branch

    def _url(self, path: str) -> str:
        return f"{self.BASE}{path}"

    def get_file_sha(self, repo_path: str) -> Optional[str]:
        """Return the SHA of an existing file, or None if it doesn't exist."""
        url = self._url(f"/repos/{self.username}/{self.repo}/contents/{repo_path}")
        r = requests.get(url, headers=self.headers, params={"ref": self.branch})
        if r.status_code == 200:
            return r.json().get("sha")
        return None

    def put_file(self, repo_path: str, content_bytes: bytes, message: str, sha: Optional[str] = None) -> bool:
        """Create or update a file. Returns True on success."""
        url = self._url(f"/repos/{self.username}/{self.repo}/contents/{repo_path}")
        payload = {
            "message": message,
            "content": base64.b64encode(content_bytes).decode(),
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha
        r = requests.put(url, headers=self.headers, json=payload)
        if r.status_code in (200, 201):
            return True
        log.error("Failed to upload %s — %s: %s", repo_path, r.status_code, r.text[:200])
        return False

    def ensure_repo_exists(self) -> bool:
        """Check that the repo is accessible."""
        url = self._url(f"/repos/{self.username}/{self.repo}")
        r = requests.get(url, headers=self.headers)
        return r.status_code == 200

    def create_repo(self, private: bool = False) -> bool:
        """Create the repository if it doesn't exist."""
        url = self._url("/user/repos")
        payload = {"name": self.repo, "private": private, "auto_init": True}
        r = requests.post(url, headers=self.headers, json=payload)
        if r.status_code == 201:
            log.info("Created new repo: %s/%s", self.username, self.repo)
            return True
        log.error("Could not create repo: %s", r.text[:200])
        return False


# ── Local file discovery ───────────────────────────────────────────────────────
def collect_files(library_path: Path, extensions: list, ignore_dirs: list, max_mb: float):
    """Yield (abs_path, relative_repo_path) for all matching files."""
    exts = {e.lower() for e in extensions} if extensions else None
    ignore = set(ignore_dirs)
    max_bytes = int(max_mb * 1024 * 1024)

    for root, dirs, files in os.walk(library_path):
        # Prune ignored directories in-place
        dirs[:] = [d for d in dirs if d not in ignore]

        for fname in files:
            if exts and Path(fname).suffix.lower() not in exts:
                continue
            abs_path = Path(root) / fname
            if abs_path.stat().st_size > max_bytes:
                log.warning("Skipping large file: %s", abs_path)
                continue
            rel = abs_path.relative_to(library_path)
            yield abs_path, str(rel).replace("\\", "/")   # GitHub paths use /


def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Main sync logic ────────────────────────────────────────────────────────────
def run_sync(cfg: dict) -> dict:
    stats = {"uploaded": 0, "skipped": 0, "failed": 0, "total": 0}
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = cfg["commit_message"].format(date=date_str)

    # Validate config
    for field in ("github_token", "github_username", "repo_name", "library_path"):
        if not cfg.get(field):
            log.error("Missing required config: %s. Run --setup first.", field)
            sys.exit(1)

    library = Path(cfg["library_path"]).expanduser().resolve()
    if not library.is_dir():
        log.error("Library path does not exist: %s", library)
        sys.exit(1)

    api = GitHubAPI(cfg["github_token"], cfg["github_username"], cfg["repo_name"], cfg["branch"])

    # Ensure repo exists
    if not api.ensure_repo_exists():
        log.warning("Repo not found — attempting to create it...")
        if not api.create_repo():
            log.error("Cannot access or create repo. Check your token and repo name.")
            sys.exit(1)

    log.info("Starting sync: %s → %s/%s @ %s", library, cfg["github_username"], cfg["repo_name"], cfg["branch"])

    cache_file = Path(__file__).parent / ".sync_cache.json"
    cache: dict = json.loads(cache_file.read_text()) if cache_file.exists() else {}

    for abs_path, repo_path in collect_files(library, cfg["extensions"], cfg["ignore_dirs"], cfg["max_file_size_mb"]):
        stats["total"] += 1
        md5 = file_md5(abs_path)

        # Skip if file hasn't changed since last sync
        if cache.get(repo_path) == md5:
            stats["skipped"] += 1
            continue

        if cfg["dry_run"]:
            log.info("[DRY-RUN] Would upload: %s", repo_path)
            stats["uploaded"] += 1
            continue

        sha = api.get_file_sha(repo_path)
        content = abs_path.read_bytes()

        if api.put_file(repo_path, content, commit_msg, sha=sha):
            log.info("✅  %s", repo_path)
            cache[repo_path] = md5
            stats["uploaded"] += 1
        else:
            stats["failed"] += 1

    # Persist cache
    if not cfg["dry_run"]:
        cache_file.write_text(json.dumps(cache, indent=2))

    log.info(
        "Sync complete — %d uploaded, %d skipped (unchanged), %d failed, %d total",
        stats["uploaded"], stats["skipped"], stats["failed"], stats["total"],
    )
    return stats


# ── Interactive setup wizard ───────────────────────────────────────────────────
def run_setup():
    print("\n" + "=" * 55)
    print("  GitHub Library Sync Agent — Setup Wizard")
    print("=" * 55 + "\n")

    cfg = load_config()

    def ask(prompt, key, secret=False):
        current = cfg.get(key, "")
        display = f"[{current}]" if current and not secret else ("[set]" if current else "[not set]")
        val = input(f"  {prompt} {display}: ").strip()
        if val:
            cfg[key] = val

    ask("GitHub Personal Access Token (repo scope):", "github_token", secret=True)
    ask("GitHub username:", "github_username")
    ask("Repository name (will be created if missing):", "repo_name")
    ask("Path to your programs library:", "library_path")
    ask("Branch name:", "branch")

    save_config(cfg)
    print("\n✅  Config saved! Run the sync with:  python github_sync.py --run\n")


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="GitHub Library Sync Agent")
    parser.add_argument("--setup",   action="store_true", help="Interactive setup wizard")
    parser.add_argument("--run",     action="store_true", help="Run sync now")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    args = parser.parse_args()

    if args.setup:
        run_setup()
    elif args.run or args.dry_run:
        cfg = load_config()
        if args.dry_run:
            cfg["dry_run"] = True
        run_sync(cfg)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
