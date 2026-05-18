"""
queries.py  —  Author 2
Owns all query logic for the music playlist application.

Every function accepts a conn argument (a sqlite3.Connection) and returns
results as a list of rows.  This module does NOT import from schema_data.py
or main.py; all database access is through the conn argument.
"""

import sqlite3


def get_playlist_tracks(conn, playlist_name):
    """Return every track on the named playlist, ordered by position ascending.

    Each row: (title, artist_name, duration_seconds, position)
    Joins PlaylistTrack → Track → Artist → Playlist.
    """
    query = """
        SELECT  t.title,
                a.name        AS artist_name,
                t.duration_seconds,
                pt.position
        FROM    PlaylistTrack pt
        JOIN    Track    t  ON pt.track_id    = t.track_id
        JOIN    Artist   a  ON t.artist_id    = a.artist_id
        JOIN    Playlist p  ON pt.playlist_id = p.playlist_id
        WHERE   p.playlist_name = ?
        ORDER BY pt.position ASC
    """
    return conn.execute(query, (playlist_name,)).fetchall()


def get_tracks_on_no_playlist(conn):
    """Return all tracks that do not appear on any playlist.

    Uses a LEFT JOIN between Track and PlaylistTrack, keeping only rows
    where the PlaylistTrack side IS NULL (i.e., no match was found).
    Each row: (title, artist_name, duration_seconds)
    """
    query = """
        SELECT  t.title,
                a.name  AS artist_name,
                t.duration_seconds
        FROM    Track t
        JOIN    Artist       a  ON t.artist_id    = a.artist_id
        LEFT JOIN PlaylistTrack pt ON t.track_id  = pt.track_id
        WHERE   pt.track_id IS NULL
        ORDER BY t.title ASC
    """
    return conn.execute(query).fetchall()


def get_most_added_track(conn):
    """Return the single track that appears on the greatest number of playlists.

    Groups PlaylistTrack by track_id, counts appearances, and returns the top
    result.  Row: (title, artist_name, playlist_count)
    """
    query = """
        SELECT  t.title,
                a.name  AS artist_name,
                COUNT(pt.playlist_id) AS playlist_count
        FROM    PlaylistTrack pt
        JOIN    Track  t ON pt.track_id  = t.track_id
        JOIN    Artist a ON t.artist_id  = a.artist_id
        GROUP BY pt.track_id
        ORDER BY playlist_count DESC
        LIMIT 1
    """
    return conn.execute(query).fetchall()


def get_playlist_durations(conn):
    """Return each playlist's name and total duration in minutes, descending.

    SUM(duration_seconds) / 60.0 gives fractional minutes; formatting
    into MM:SS is handled by the caller (main.py).
    Row: (playlist_name, total_seconds)
    """
    query = """
        SELECT  p.playlist_name,
                SUM(t.duration_seconds) AS total_seconds
        FROM    Playlist p
        JOIN    PlaylistTrack pt ON p.playlist_id = pt.playlist_id
        JOIN    Track         t  ON pt.track_id   = t.track_id
        GROUP BY p.playlist_id
        ORDER BY total_seconds DESC
    """
    return conn.execute(query).fetchall()


# ---------------------------------------------------------------------------
# Isolated smoke-test (does NOT depend on schema_data or main)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    conn = sqlite3.connect("music.db")
    conn.execute("PRAGMA foreign_keys = ON;")

    print("=== Tracks on 'Late Night Drives' ===")
    rows = get_playlist_tracks(conn, "Late Night Drives")
    for r in rows:
        print(r)

    print("\n=== Tracks on No Playlist ===")
    rows = get_tracks_on_no_playlist(conn)
    for r in rows:
        print(r)

    print("\n=== Most-Added Track ===")
    rows = get_most_added_track(conn)
    for r in rows:
        print(r)

    print("\n=== Playlist Durations ===")
    rows = get_playlist_durations(conn)
    for r in rows:
        print(r)

    conn.close()
