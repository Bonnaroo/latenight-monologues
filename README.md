# latenight-monologues

Auto-curator: polls late-night show YouTube channels every 3.5 hours, filters for monologue clips by title, and adds them newest-first to per-show playlists on a dedicated Brand channel. Tracks processed IDs so nothing is added twice.

## Quick start

1. Create your Brand channel and 5 playlists (one per show).
2. 2. Set up a Google Cloud project, enable YouTube Data API v3, create OAuth 2.0 Desktop credentials, download as `client_secret.json`.
   3. 3. Fill in `config.py`: set `TARGET_CHANNEL_ID` and each show's `playlist_id`.
      4. 4. `pip install -r requirements.txt`
         5. 5. `python curator.py` — browser opens for OAuth consent (choose Brand channel account). Token saved to `token.json` (gitignored).
            6. 6. `python curator.py --loop` — runs continuously, polling every 3h 30m.
              
               7. ## Shows and filters
              
               8. | Show | Positive filter | Notes |
               9. |------|----------------|-------|
               10. | Jimmy Kimmel Live | "monologue" in title | |
               11. | The Tonight Show Starring Jimmy Fallon | "monologue" in title | |
               12. | Late Night with Seth Meyers | "monologue" or "a closer look" in title | |
               13. | The Daily Show | title ends with "| The Daily Show" | Excludes Klepper, Grace, Foxsplains, extended interviews, etc. |
               14. | Real Time with Bill Maher | "monologue" or "new rules" in title | Weekly (Fridays) |
              
               15. Tune filters in `config.py` — `title_filters` (OR match) and `exclude_keywords` (AND NOT match).
              
               16. ## API quota
              
               17. ~250 units/run (50 items x 5 shows). YouTube Data API v3 free quota: 10,000 units/day — headroom for 40 runs/day.
              
               18. ## Files
              
               19. | File | Purpose |
               20. |------|---------|
               21. | `curator.py` | Main script |
               22. | `config.py` | Show list, playlist IDs, filter keywords — edit this |
               23. | `requirements.txt` | Python dependencies |
               24. | `.env.example` | Template for environment vars |
               25. | `state.json` | Processed video ID log (gitignored, auto-created) |
               26. | `token.json` | OAuth token (gitignored, auto-created on first run) |
               27. | `client_secret.json` | OAuth client credentials from Google Cloud (gitignored, you provide) |
