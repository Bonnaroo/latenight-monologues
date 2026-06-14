#!/usr/bin/env python3
"""
curator.py
Late-night monologue auto-curator.

Reads each show's YouTube uploads playlist, filters clips whose titles match
the show's monologue patterns, and adds matched clips (newest-first) to the
corresponding playlist on the configured Brand channel.

Tracked video IDs are persisted in state.json so nothing is added twice.

Usage:
    python curator.py          # single run
        python curator.py --loop   # poll every POLL_INTERVAL_SECONDS
        """

import argparse
import json
import logging
import os
import re
import time
from datetime import timedelta
from pathlib import Path

import isodate
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config

logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s  %(levelname)-8s  %(message)s",
      datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_credentials():
      """Return valid OAuth2 credentials, refreshing or re-authorising as needed."""
      creds = None
      token_path = Path(config.TOKEN_FILE)

    if token_path.exists():
              creds = Credentials.from_authorized_user_file(str(token_path), config.SCOPES)

    if not creds or not creds.valid:
              if creds and creds.expired and creds.refresh_token:
                            log.info("Refreshing access token ...")
                            creds.refresh(Request())
    else:
            log.info("Launching OAuth flow (browser will open) ...")
                  flow = InstalledAppFlow.from_client_secrets_file(
                                    os.environ.get("CLIENT_SECRETS_FILE", "client_secret.json"),
                                    config.SCOPES,
                  )
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())
        log.info("Credentials saved to %s", token_path)

    return creds


def build_youtube():
      return build("youtube", "v3", credentials=get_credentials())

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def load_state():
      """Return {show_name: set(video_id)} from state file."""
    path = Path(config.STATE_FILE)
    if not path.exists():
              return {}
          raw = json.loads(path.read_text())
    return {k: set(v) for k, v in raw.items()}


def save_state(state):
      path = Path(config.STATE_FILE)
    path.write_text(json.dumps({k: list(v) for k, v in state.items()}, indent=2))

# ---------------------------------------------------------------------------
# Title filtering
# ---------------------------------------------------------------------------

def matches_show(title: str, show: dict) -> bool:
      """
          Return True if `title` matches the show's monologue filter rules.

              Logic:
                    - title (lowercased) must contain at least one string from title_filters (OR)
                          - title must NOT contain any string from exclude_keywords (AND NOT)
                              """
    t = title.lower()

    # Must match at least one include filter
    if not any(f.lower() in t for f in show["title_filters"]):
              return False

    # Must not match any exclude keyword
    if any(k.lower() in t for k in show.get("exclude_keywords", [])):
              return False

    return True

# ---------------------------------------------------------------------------
# YouTube helpers
# ---------------------------------------------------------------------------

def get_uploads(youtube, uploads_playlist_id: str, max_results: int):
      """
          Yield (video_id, title, published_at) tuples from an uploads playlist,
              newest first, up to max_results items.
                  """
      request = youtube.playlistItems().list(
          part="snippet",
          playlistId=uploads_playlist_id,
          maxResults=min(max_results, 50),
      )
      response = request.execute()

    for item in response.get("items", []):
              snippet = item["snippet"]
              vid_id = snippet["resourceId"]["videoId"]
              title = snippet["title"]
              published_at = snippet.get("publishedAt", "")
              yield vid_id, title, published_at


def get_video_duration_seconds(youtube, video_id: str) -> int:
      """Return the duration in seconds for a single video. Returns 0 on error."""
      try:
                resp = youtube.videos().list(part="contentDetails", id=video_id).execute()
                items = resp.get("items", [])
                if not items:
                              return 0
                          duration_str = items[0]["contentDetails"]["duration"]
                return int(isodate.parse_duration(duration_str).total_seconds())
except Exception as exc:
        log.warning("Could not fetch duration for %s: %s", video_id, exc)
        return 0


def playlist_insert(youtube, playlist_id: str, video_id: str, position: int = 0):
      """Insert video_id at the top of playlist_id (position 0 = newest on top)."""
      youtube.playlistItems().insert(
          part="snippet",
          body={
              "snippet": {
                  "playlistId": playlist_id,
                  "resourceId": {
                      "kind": "youtube#video",
                      "videoId": video_id,
                  },
                  "position": position,
              }
          },
      ).execute()

# ---------------------------------------------------------------------------
# Core run logic
# ---------------------------------------------------------------------------

def run_once(youtube, state: dict) -> dict:
      """
          Iterate over all configured shows, find new monologue clips, add to playlists.
              Returns updated state dict.
                  """
      for show in config.SHOWS:
                name = show["name"]
                uploads_pl = show["uploads_playlist"]
                dest_pl = show["playlist_id"]

          if not dest_pl:
                        log.warning("[%s] playlist_id not set in config.py -- skipping", name)
                        continue

        log.info("[%s] Checking uploads playlist %s ...", name, uploads_pl)
        seen = state.setdefault(name, set())

        # Collect matching unseen videos (preserving upload order = newest first)
        new_clips = []
        try:
                      for vid_id, title, published_at in get_uploads(
                                        youtube, uploads_pl, config.MAX_RESULTS_PER_SHOW
                      ):
                                        if vid_id in seen:
                                                              continue
                                                          if not matches_show(title, show):
                                                                                log.debug("[%s] SKIP  %s | %s", name, vid_id, title)
                                                                                continue

                                        # Optional duration filter
                                        if config.ENABLE_DURATION_FILTER:
                                                              dur = get_video_duration_seconds(youtube, vid_id)
                                                              if dur < config.MIN_DURATION_SECONDS:
                                                                                        log.info(
                                                                                                                      "[%s] SKIP (too short: %ds)  %s | %s",
                                                                                                                      name, dur, vid_id, title,
                                                                                          )
                                                                                        seen.add(vid_id)
                                                                                        continue

                                                          log.info("[%s] MATCH %s | %s", name, vid_id, title)
                new_clips.append((vid_id, title))

except HttpError as exc:
            log.error("[%s] API error reading uploads: %s", name, exc)
            continue

        if not new_clips:
                      log.info("[%s] No new monologue clips found.", name)
            continue

        # Insert newest-first: iterate in reverse so position=0 ends up being
        # the most recent clip at the top of the playlist.
        for vid_id, title in reversed(new_clips):
                      try:
                                        playlist_insert(youtube, dest_pl, vid_id, position=0)
                                        seen.add(vid_id)
                                        log.info("[%s] ADDED  %s | %s", name, vid_id, title)
except HttpError as exc:
                log.error("[%s] Failed to add %s: %s", name, vid_id, exc)

    return state

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
      parser = argparse.ArgumentParser(description="Late-night monologue curator")
    parser.add_argument(
              "--loop",
              action="store_true",
              help="Poll continuously every POLL_INTERVAL_SECONDS (default: single run)",
    )
    args = parser.parse_args()

    youtube = build_youtube()
    state = load_state()

    if args.loop:
              log.info(
                            "Starting polling loop (interval: %s) ...",
                            str(timedelta(seconds=config.POLL_INTERVAL_SECONDS)),
              )
        while True:
                      state = run_once(youtube, state)
            save_state(state)
            log.info(
                              "Run complete. Sleeping %s ...",
                              str(timedelta(seconds=config.POLL_INTERVAL_SECONDS)),
            )
            time.sleep(config.POLL_INTERVAL_SECONDS)
else:
        state = run_once(youtube, state)
        save_state(state)
        log.info("Single run complete.")


if __name__ == "__main__":
      main()
