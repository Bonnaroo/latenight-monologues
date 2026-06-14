#!/usr/bin/env python3
"""YouTube monologue auto-curator.

Fetches uploads for each configured show, filters by title keywords,
and adds new matching videos to a target playlist. Tracks processed
video IDs in state.json to avoid duplicates.
"""

import json
import os
import sys

import requests

from config import SHOWS

TOKEN_URL = "https://oauth2.googleapis.com/token"
PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
STATE_FILE = "state.json"


def get_access_token():
    """Exchange the refresh token for a short-lived access token."""
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("Missing one or more required env vars: "
              "YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, "
              "YOUTUBE_REFRESH_TOKEN", file=sys.stderr)
        sys.exit(1)

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    resp = requests.post(TOKEN_URL, data=payload, timeout=30)
    if not resp.ok:
        print(f"Token request failed: {resp.status_code} {resp.text}",
              file=sys.stderr)
        sys.exit(1)

    return resp.json()["access_token"]


def load_state():
    """Load the set of already-processed video IDs."""
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("processed_video_ids", []))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Could not read {STATE_FILE}: {exc}", file=sys.stderr)
        return set()


def save_state(processed_ids):
    """Persist the set of processed video IDs back to disk."""
    data = {"processed_video_ids": sorted(processed_ids)}
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def fetch_uploads(access_token, uploads_playlist_id):
    """Return all items from a show's uploads playlist (paginated)."""
    headers = {"Authorization": f"Bearer {access_token}"}
    items = []
    page_token = None

    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(
            PLAYLIST_ITEMS_URL, headers=headers, params=params, timeout=30
        )
        if not resp.ok:
            print(f"Failed to fetch uploads for {uploads_playlist_id}: "
                  f"{resp.status_code} {resp.text}", file=sys.stderr)
            break

        body = resp.json()
        items.extend(body.get("items", []))

        page_token = body.get("nextPageToken")
        if not page_token:
            break

    return items


def title_matches(title, title_filters, exclude_keywords):
    """Check title against include filters and exclude keywords."""
    lowered = title.lower()

    included = any(f.lower() in lowered for f in title_filters)
    if not included:
        return False

    excluded = any(k.lower() in lowered for k in exclude_keywords)
    if excluded:
        return False

    return True


def add_to_playlist(access_token, target_playlist_id, video_id):
    """Insert a video at position 0 of the target playlist."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    params = {"part": "snippet"}
    body = {
        "snippet": {
            "playlistId": target_playlist_id,
            "position": 0,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id,
            },
        }
    }

    resp = requests.post(
        PLAYLIST_ITEMS_URL,
        headers=headers,
        params=params,
        json=body,
        timeout=30,
    )
    if not resp.ok:
        print(f"Failed to add {video_id} to {target_playlist_id}: "
              f"{resp.status_code} {resp.text}", file=sys.stderr)
        return False

    return True


def process_show(access_token, show, processed_ids):
    """Process a single show; returns count of newly added videos."""
    name = show.get("name", show.get("uploads_playlist_id", "unknown"))
    title_filters = show.get("title_filters", [])
    exclude_keywords = show.get("exclude_keywords", [])
    uploads_playlist_id = show["uploads_playlist_id"]
    target_playlist_id = show["target_playlist_id"]

    print(f"Processing show: {name}")
    items = fetch_uploads(access_token, uploads_playlist_id)

    added = 0
    for item in items:
        snippet = item.get("snippet", {})
        title = snippet.get("title", "")

        resource = snippet.get("resourceId", {})
        video_id = resource.get("videoId")
        if not video_id:
            video_id = item.get("contentDetails", {}).get("videoId")
        if not video_id:
            continue

        if video_id in processed_ids:
            continue

        if not title_matches(title, title_filters, exclude_keywords):
            processed_ids.add(video_id)
            continue

        if add_to_playlist(access_token, target_playlist_id, video_id):
            print(f"  Added: {title} ({video_id})")
            added += 1

        processed_ids.add(video_id)

    return added


def main():
    access_token = get_access_token()
    processed_ids = load_state()

    total_added = 0
    for show in SHOWS:
        total_added += process_show(access_token, show, processed_ids)

    save_state(processed_ids)
    print(f"Done. {total_added} new video(s) added. "
          f"{len(processed_ids)} total tracked.")


if __name__ == "__main__":
    main()
