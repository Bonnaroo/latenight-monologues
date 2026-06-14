# config.py - Show/playlist configuration. Edit title_filters and exclude_keywords to tune.

TARGET_CHANNEL_ID = "UC0rbsni42J4q-utj4z61OBw"  # Late Night Monologues brand channel

SHOWS = [
    {
        "name": "Jimmy Kimmel Live",
        "channel_id": "UCa6vGFO9ty8v5KZJXQxdhaw",
        "uploads_playlist_id": "UUa6vGFO9ty8v5KZJXQxdhaw",
        "target_playlist_id": "PLG-wspfcFzusYZoAOzkErgSPhKq4ETmUd",
        "title_filters": ["monologue"],
        "exclude_keywords": [],
    },
    {
        "name": "The Tonight Show Starring Jimmy Fallon",
        "channel_id": "UC8-Th83bH_thdKZDJCrn88g",
        "uploads_playlist_id": "UU8-Th83bH_thdKZDJCrn88g",
        "target_playlist_id": "PLG-wspfcFzuu9GPymaM3qo8muDXSJggtv",
        "title_filters": ["monologue"],
        "exclude_keywords": [],
    },
    {
        "name": "Late Night with Seth Meyers",
        "channel_id": "UCVTyTA7-g9nopHeHbeuvpRA",
        "uploads_playlist_id": "UUVTyTA7-g9nopHeHbeuvpRA",
        "target_playlist_id": "PLG-wspfcFzutOI_my6jt5bY1RDofWPdoX",
        "title_filters": ["monologue", "a closer look"],
        "exclude_keywords": [],
    },
    {
        "name": "The Daily Show",
        "channel_id": "UCwWhs_6x42TyRM4Wstoq8HA",
        "uploads_playlist_id": "UUwWhs_6x42TyRM4Wstoq8HA",
        "target_playlist_id": "PLG-wspfcFzuvu7Poqlce1-O7FVxRE-368",
        "title_filters": ["monologue", "headlines"],
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
        "uploads_playlist_id": "UUy6kyFxaMqGtpE3pQTflK8A",
        "target_playlist_id": "PLG-wspfcFzut6oPHV4wOJXHXiXFG7tF09",
        "title_filters": ["monologue", "new rules"],
        "exclude_keywords": [],
    },
]
