"""
main.py  —  Integrator
Driver for the music playlist application.

Startup logic:
  • If music.db exists on disk  →  open it directly (re-open mode).
  • Otherwise                   →  build + seed an in-memory DB, back it up
                                   to music.db, then open that file.

All subsequent work uses the file-backed connection so data persists.
"""

import os
import sqlite3

from schema_data import build_database, seed_database
from queries import (
    get_playlist_tracks,
    get_tracks_on_no_playlist,
    get_most_added_track,
    get_playlist_durations,
)

DB_PATH = "music.db"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_duration(seconds):
    """Convert an integer number of seconds to a 'M:SS' string."""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def print_table(headers, rows, col_widths=None):
    """Print a simple fixed-width table to stdout."""
    if not rows:
        print("  (no results)\n")
        return

    # Auto-compute widths if not provided
    if col_widths is None:
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in col_widths)
    sep = "  " + "  ".join("-" * w for w in col_widths)

    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))
    print()


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def open_connection():
    """Return a connection to music.db, building it on first run if needed."""
    if os.path.exists(DB_PATH):
        print(f"[startup] Existing database found — opening {DB_PATH}.")
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    print("[startup] No database found — building from scratch.")
    mem = sqlite3.connect(":memory:")
    build_database(mem)
    seed_database(mem)

    target = sqlite3.connect(DB_PATH)
    mem.backup(target)
    target.close()
    mem.close()

    print(f"[startup] Database written to {DB_PATH}.")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------

def show_playlist_tracks(conn):
    rows = conn.execute("SELECT playlist_name FROM Playlist ORDER BY playlist_name").fetchall()
    if not rows:
        print("No playlists found.\n")
        return

    print("\nAvailable playlists:")
    for i, (name,) in enumerate(rows, 1):
        print(f"  {i}. {name}")

    choice = input("Enter playlist number: ").strip()
    try:
        idx = int(choice) - 1
        playlist_name = rows[idx][0]
    except (ValueError, IndexError):
        print("Invalid choice.\n")
        return

    results = get_playlist_tracks(conn, playlist_name)
    print(f"\n  === {playlist_name} ===")
    formatted = [
        (r[0], r[1], fmt_duration(r[2]), r[3])
        for r in results
    ]
    print_table(
        ["Title", "Artist", "Duration", "Pos"],
        formatted,
        col_widths=[30, 20, 8, 4],
    )


def show_tracks_on_no_playlist(conn):
    results = get_tracks_on_no_playlist(conn)
    print("\n  === Tracks Not on Any Playlist ===")
    formatted = [(r[0], r[1], fmt_duration(r[2])) for r in results]
    print_table(["Title", "Artist", "Duration"], formatted, [30, 20, 8])


def show_most_added_track(conn):
    results = get_most_added_track(conn)
    print("\n  === Most-Added Track ===")
    print_table(["Title", "Artist", "# Playlists"], results, [30, 20, 11])


def show_playlist_durations(conn):
    results = get_playlist_durations(conn)
    print("\n  === Playlist Total Durations ===")
    formatted = [(r[0], fmt_duration(r[1])) for r in results]
    print_table(["Playlist", "Total Duration"], formatted, [22, 14])


def delete_artist(conn):
    """Prompt for an artist and remove them with all dependent records."""
    rows = conn.execute(
        "SELECT artist_id, name FROM Artist ORDER BY name"
    ).fetchall()

    if not rows:
        print("No artists in the database.\n")
        return

    print("\nArtists:")
    for aid, name in rows:
        print(f"  [{aid}] {name}")

    choice = input("Enter artist ID to delete: ").strip()
    try:
        artist_id = int(choice)
    except ValueError:
        print("Invalid ID.\n")
        return

    # Confirm the artist exists
    artist = conn.execute(
        "SELECT name FROM Artist WHERE artist_id = ?", (artist_id,)
    ).fetchone()
    if not artist:
        print(f"No artist with ID {artist_id}.\n")
        return

    confirm = input(
        f"Delete '{artist[0]}' and ALL their tracks/playlist entries? (yes/no): "
    ).strip().lower()
    if confirm != "yes":
        print("Deletion cancelled.\n")
        return

    try:
        # Step 1 — remove PlaylistTrack rows for this artist's tracks
        conn.execute("""
            DELETE FROM PlaylistTrack
            WHERE track_id IN (
                SELECT track_id FROM Track WHERE artist_id = ?
            )
        """, (artist_id,))

        # Step 2 — remove the artist's Track rows
        conn.execute(
            "DELETE FROM Track WHERE artist_id = ?", (artist_id,)
        )

        # Step 3 — remove the Artist row
        conn.execute(
            "DELETE FROM Artist WHERE artist_id = ?", (artist_id,)
        )

        conn.commit()
        print(f"Artist '{artist[0]}' and all dependent records removed.\n")

    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"Deletion failed due to IntegrityError: {e}\n")


# ---------------------------------------------------------------------------
# Menu loop
# ---------------------------------------------------------------------------

MENU = """
╔══════════════════════════════════════╗
║       Music Playlist Manager         ║
╠══════════════════════════════════════╣
║  1. Show all tracks on a playlist    ║
║  2. Show tracks on no playlist       ║
║  3. Show most-added track            ║
║  4. Show playlist durations          ║
║  5. Delete an artist (cascade)       ║
║  0. Exit                             ║
╚══════════════════════════════════════╝
"""

def run():
    conn = open_connection()
    print()

    while True:
        print(MENU)
        choice = input("Select an option: ").strip()

        if choice == "1":
            show_playlist_tracks(conn)
        elif choice == "2":
            show_tracks_on_no_playlist(conn)
        elif choice == "3":
            show_most_added_track(conn)
        elif choice == "4":
            show_playlist_durations(conn)
        elif choice == "5":
            delete_artist(conn)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid option — please enter 0–5.\n")

    conn.close()


if __name__ == "__main__":
    run()
