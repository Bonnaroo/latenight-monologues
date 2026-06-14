#!/usr/bin/env python3
"""
curator.py
Late-night monologue auto-curator.

Reads each show's YouTube uploads playlist, filters clips whose titles match
the show's monologue patterns, and adds matched clips (newest-first) to the
corresponding playlist on the configured Brand channel.

Auth: uses a stored OAuth refresh token (YOUTUBE_REFRESH_TOKEN env var) so it
runs headlessly in GitHub Actions with no browser interaction.

Tracked video IDs are persisted in state.json so nothing is added twice.
In GitHub Actions, state.json is committed back to the repo each run.
"""

import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

from config import SHOWS, TARGET_CHANNEL_ID, POLL_INTERVAL_SECONDS, STATE_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OAuth helpers (refresh-token flow — no browser required)
# ---------------------------------------------------------------------------

TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"


def get_access_token() -> str:
    """Exchange the stored refresh token for a short-lived access token."""
    client_id     = os.environ["YOUTUBE_CLIENT_ID"]
    client_secret = os.environ["YOUTUBE_CLIENT_SECRET"]
    refresh_token = os.environ["YOUTUBE_REFRESH_TOKEN"]

    resp = requests.post(TOKEN_URL, data={
        "client_id":     client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type":    "refresh_token",
    }, timeout=30)
        print(f"DEBUG client_id={client_id[:20]!r} token_len={len(refresh_token)}", flush=True)
    if not resp.ok:
        print(f"Token error {resp.status_code}: {resp.text}", flush=True)
    resp.raise_for_status()
    return resp.json()["access_token"]


def yt_get(access_token: str, endpoint: str, params: dict) -> dict:
    """GET a YouTube Data API v3 endpoint."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(f"{YOUTUBE_API}/{endpoint}", params=params,
                        headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def yt_post(access_token: str, endpoint: str, body: dict) -> dict:
    """POST to a YouTube Data API v3 endpoint."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/json",
    }
    resp = requests.post(f"{YOUTUBE_API}/{endpoint}", json=body,
                         headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def load_state(path: str) -> dict:
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text())
    return {}


def save_state(state: dict, path: str) -> None:
    Path(path).write_text(json.dumps(state, indent=2))


def title_matches(title: str, show: dict) -> bool:
    """Return True if the title matches any title_filter and no exclude_keyword."""
    t = title.lower()
    if not any(f.lower() in t for f in show["title_filters"]):
        return False
    if any(e.lower() in t for e in show.get("exclude_keywords", [])):
        return False
    return True


def fetch_recent_uploads(access_token: str, uploads_playlist_id: str,
                         max_results: int = 50) -> list[dict]:
    """Return up to max_results recent items from an uploads playlist."""
    items, page_token = [], None
    while True:
        params = {
            "part":       "snippet",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        data = yt_get(access_token, "playlistItems", params)
        items.extend(data.get("items", []))
        if len(items) >= max_results:
            break
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return items[:max_results]


def add_to_playlist(access_token: str, playlist_id: str, video_id: str) -> None:
    """Insert a video at position 0 (top) of the target playlist."""
    yt_post(access_token, "playlistItems", {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind":    "youtube#video",
                "videoId": video_id,
            },
            "position": 0,
        }
    })


def run_once(access_token: str, state: dict) -> dict:
    """One full pass: check all shows, add new monologues, return updated state."""
    for show in SHOWS:
        name        = show["name"]
        playlist_id = show.get("playlist_id", "")
        if not playlist_id:
            log.warning("%s: no playlist_id configured, skipping", name)
            continue

        log.info("Checking %s ...", name)
        seen = set(state.get(name, []))

        try:
            items = fetch_recent_uploads(access_token, show["uploads_playlist"])
        except Exception as exc:
            log.error("%s: failed to fetch uploads — %s", name, exc)
            continue

        added = 0
        # Process oldest-first so newest ends up at position 0
        for item in reversed(items):
            snippet  = item.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId", "")
            title    = snippet.get("title", "")

            if not video_id or video_id in seen:
                continue
            if not title_matches(title, show):
                continue

            try:
                add_to_playlist(access_token, playlist_id, video_id)
                seen.add(video_id)
                added += 1
                log.info("  + %s  [%s]", title, video_id)
            except Exception as exc:
                log.error("  ! Failed to add %s: %s", video_id, exc)

        state[name] = list(seen)
        log.info("%s: added %d new clip(s)", name, added)

    return state


def main() -> None:
    missing = [v for v in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET",
                           "YOUTUBE_REFRESH_TOKEN")
               if not os.environ.get(v)]
    if missing:
        log.error("Missing environment variables: %s", ", ".join(missing))
        sys.exit(1)

    state = load_state(STATE_FILE)
    access_token = get_access_token()
    state = run_once(access_token, state)
    save_state(state, STATE_FILE)
    log.info("Done.")


if __name__ == "__main__":
    main()
