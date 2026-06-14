# config.py - Show/playlist configuration. Edit title_filters and exclude_keywords to tune.

TARGET_CHANNEL_ID = "UC0rbsni42J4q-utj4z61OBw"  # From youtube.com/account_advanced

SHOWS = [
      {
                "name": "Jimmy Kimmel Live",
                "channel_id": "UCa6vGFO9ty8v5KZJXQxdhaw",
                "uploads_playlist": "UUa6vGFO9ty8v5KZJXQxdhaw",
                "playlist_id": "PLG-wspfcFzusYZoAOzkErgSPhKq4ETmUd",
                "title_filters": ["monologue"],
                "exclude_keywords": [],
      },
      {
                "name": "The Tonight Show Starring Jimmy Fallon",
                "channel_id": "UC8-Th83bH_thdKZDJCrn88g",
                "uploads_playlist": "UU8-Th83bH_thdKZDJCrn88g",
                "playlist_id": "PLG-wspfcFzuu9GPymaM3qo8muDXSJggtv",
                "title_filters": ["monologue"],
                "exclude_keywords": [],
      },
      {
                "name": "Late Night with Seth Meyers",
                "channel_id": "UCVTyTA7-g9nopHeHbeuvpRA",
                "uploads_playlist": "UUVTyTA7-g9nopHeHbeuvpRA",
                "playlist_id": "PLG-wspfcFzutOI_my6jt5bY1RDofWPdoX",
                "title_filters": ["monologue", "a closer look"],
                "exclude_keywords": [],
      },
      {
                "name": "The Daily Show",
                "channel_id": "UCwWhs_6x42TyRM4Wstoq8HA",
                "uploads_playlist": "UUwWhs_6x42TyRM4Wstoq8HA",
                "playlist_id": "PLG-wspfcFzuvu7Poqlce1-O7FVxRE-368",
                # Main desk commentary clips end with "| The Daily Show".
                # Negative list excludes field pieces, correspondent franchises, interviews.
                # Tune exclude_keywords if interview clips slip through.
                "title_filters": ["| the daily show"],
                "exclude_keywords": [
                              "klepper", "fingers the pulse", "grace kuhlenschmidt",
                              "foxsplains", "extended interview", "between the scenes",
                              "your moment of zen", "ears edition", "after the cut",
                              "dailyshowography", "midterm anal",
                ],
      },
      {
                "name": "Real Time with Bill Maher",
                "channel_id": "UCy6kyFxaMqGtpE3pQTflK8A",
                "uploads_playlist": "UUy6kyFxaMqGtpE3pQTflK8A",
                "playlist_id": "PLG-wspfcFzut6oPHV4wOJXHXiXFG7tF09",
                "title_filters": ["monologue", "new rules"],
                "exclude_keywords": [],
      },
]

POLL_INTERVAL_SECONDS = 3 * 3600 + 30 * 60  # 3h 30m -- ~250 quota units/run, well under 10k/day limit

# Set True to also filter on video duration (skips Shorts/short clips).
# Costs 1 extra quota unit per matched video. Useful for Daily Show precision.
ENABLE_DURATION_FILTER = False
MIN_DURATION_SECONDS = 5 * 60  # 5 minutes

MAX_RESULTS_PER_SHOW = 50   # 1 quota unit per show per poll
STATE_FILE = "state.json"   # tracks processed video IDs; gitignored
TOKEN_FILE = "token.json"   # OAuth token; gitignored
SCOPES = ["https://www.googleapis.com/auth/youtube"]
