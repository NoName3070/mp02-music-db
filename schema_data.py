"""
schema_data.py  —  Author 1
Owns the database schema and all seed data for the music playlist application.
"""

import sqlite3


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def build_database(conn):
    """Create the four-table music schema with foreign-key enforcement.

    Tables are created in dependency order so that every REFERENCES clause
    points to a table that already exists:
        Artist  →  Track  →  (Playlist)  →  PlaylistTrack
    """
    conn.execute("PRAGMA foreign_keys = ON;")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS Artist (
            artist_id    INTEGER PRIMARY KEY,
            name         TEXT    NOT NULL,
            genre        TEXT    NOT NULL,
            origin_city  TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS Track (
            track_id         INTEGER PRIMARY KEY,
            title            TEXT    NOT NULL,
            duration_seconds INTEGER NOT NULL,
            artist_id        INTEGER NOT NULL
                REFERENCES Artist(artist_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS Playlist (
            playlist_id   INTEGER PRIMARY KEY,
            playlist_name TEXT    NOT NULL,
            owner_name    TEXT    NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS PlaylistTrack (
            playlist_id  INTEGER NOT NULL REFERENCES Playlist(playlist_id),
            track_id     INTEGER NOT NULL REFERENCES Track(track_id),
            position     INTEGER NOT NULL,
            PRIMARY KEY (playlist_id, track_id)
        )
    """)

    conn.commit()


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_database(conn):
    """Populate all four tables with realistic music data.

    Uses INSERT OR IGNORE so this function can be called more than once
    without raising an IntegrityError on duplicate primary keys.
    Inserts at least 6 artists, 18 tracks, 4 playlists, 20 PlaylistTrack rows.
    """

    # ---- Artists (8) -------------------------------------------------------
    artists = [
        (1, "Radiohead",          "Alternative Rock", "Oxford"),
        (2, "Kendrick Lamar",     "Hip-Hop",          "Compton"),
        (3, "Billie Eilish",      "Indie Pop",        "Los Angeles"),
        (4, "Tame Impala",        "Psychedelic Rock", "Perth"),
        (5, "FKA Twigs",          "R&B / Art Pop",    "Cheltenham"),
        (6, "Tyler, the Creator", "Hip-Hop",          "Los Angeles"),
        (7, "Lorde",              "Indie Pop",        "Auckland"),
        (8, "James Blake",        "Electronic Soul",  "London"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO Artist VALUES (?, ?, ?, ?)", artists
    )

    # ---- Tracks (20) -------------------------------------------------------
    # (track_id, title, duration_seconds, artist_id)
    tracks = [
        # Radiohead (artist 1) — 4 tracks
        (1,  "Creep",                   238, 1),
        (2,  "Karma Police",            264, 1),
        (3,  "Fake Plastic Trees",      286, 1),
        (4,  "No Surprises",            228, 1),
        # Kendrick Lamar (artist 2) — 3 tracks
        (5,  "HUMBLE.",                 177, 2),
        (6,  "Alright",                 219, 2),
        (7,  "DNA.",                    185, 2),
        # Billie Eilish (artist 3) — 3 tracks
        (8,  "bad guy",                 194, 3),
        (9,  "ocean eyes",              198, 3),
        (10, "Happier Than Ever",       298, 3),
        # Tame Impala (artist 4) — 3 tracks
        (11, "The Less I Know the Better", 216, 4),
        (12, "Let It Happen",           467, 4),
        (13, "Eventually",              316, 4),
        # FKA Twigs (artist 5) — 2 tracks
        (14, "Two Weeks",               241, 5),
        (15, "cellophane",              309, 5),
        # Tyler, the Creator (artist 6) — 2 tracks
        (16, "EARFQUAKE",               196, 6),
        (17, "See You Again",           239, 6),
        # Lorde (artist 7) — 2 tracks
        (18, "Royals",                  193, 7),
        (19, "Green Light",             236, 7),
        # James Blake (artist 8) — 1 track
        (20, "Limit to Your Love",      228, 8),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO Track VALUES (?, ?, ?, ?)", tracks
    )

    # ---- Playlists (4) -----------------------------------------------------
    playlists = [
        (1, "Late Night Drives",   "Alex"),
        (2, "Morning Energy",      "Jordan"),
        (3, "Deep Focus",          "Morgan"),
        (4, "Weekend Vibes",       "Riley"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO Playlist VALUES (?, ?, ?)", playlists
    )

    # ---- PlaylistTrack (22 assignments) ------------------------------------
    # (playlist_id, track_id, position)
    assignments = [
        # Late Night Drives (playlist 1) — 6 tracks
        (1,  2,  1),   # Karma Police
        (1,  3,  2),   # Fake Plastic Trees
        (1, 15,  3),   # cellophane
        (1, 20,  4),   # Limit to Your Love
        (1,  9,  5),   # ocean eyes
        (1, 13,  6),   # Eventually
        # Morning Energy (playlist 2) — 6 tracks
        (2,  5,  1),   # HUMBLE.
        (2,  7,  2),   # DNA.
        (2,  8,  3),   # bad guy
        (2, 11,  4),   # The Less I Know the Better
        (2, 16,  5),   # EARFQUAKE
        (2, 19,  6),   # Green Light
        # Deep Focus (playlist 3) — 5 tracks
        (3,  4,  1),   # No Surprises
        (3, 12,  2),   # Let It Happen
        (3, 14,  3),   # Two Weeks
        (3, 10,  4),   # Happier Than Ever
        (3, 20,  5),   # Limit to Your Love  ← track 20 on two playlists
        # Weekend Vibes (playlist 4) — 5 tracks
        (4,  1,  1),   # Creep
        (4,  6,  2),   # Alright
        (4, 17,  3),   # See You Again
        (4, 18,  4),   # Royals
        (4, 11,  5),   # The Less I Know the Better ← on two playlists
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO PlaylistTrack VALUES (?, ?, ?)", assignments
    )

    conn.commit()


# ---------------------------------------------------------------------------
# Standalone demonstration
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Build and seed an in-memory database
    conn = sqlite3.connect(":memory:")
    build_database(conn)
    seed_database(conn)
    print("In-memory database built and seeded.")

    # -- IntegrityError demonstration ----------------------------------------
    print("\n--- IntegrityError Demonstration ---")
    try:
        conn.execute(
            "INSERT INTO Track VALUES (99, 'Ghost Track', 210, 9999)"
        )
    except sqlite3.IntegrityError as e:
        print(f"IntegrityError caught: {e}")
        print("Explanation: artist_id 9999 does not exist in the Artist table.")
        print("SQLite rejected the insert to protect referential integrity.\n")

    # -- Persist to disk -----------------------------------------------------
    target = sqlite3.connect("music.db")
    conn.backup(target)
    target.close()
    conn.close()
    print("Database successfully written to music.db")
