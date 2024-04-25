import sqlite3

def create_connection(db_file='albums.db'):
    """Create and return a database connection and ensure tables are created."""
    conn = sqlite3.connect(db_file)  # This will create the database file if it doesn't exist
    create_tables(conn)  # Create tables if not already present
    return conn

def create_tables(conn):
    """Create the tables required for the application."""
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist TEXT NOT NULL,
            album_name TEXT NOT NULL,
            release_date TEXT,
            release_year INTEGER,
            album_url TEXT UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS album_tags (
            album_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            UNIQUE(album_id, tag_id)
        )
    ''')
    conn.commit()

def fetch_albums(conn):
    """Fetch all albums sorted by artist name."""
    c = conn.cursor()
    # Ensure the order here matches what is expected in your GUI
    c.execute("SELECT id, artist, album_name, release_date, release_year, album_url FROM albums ORDER BY artist")
    return c.fetchall()

def fetch_artists(conn):
    """Fetch all unique artists from the albums table."""
    c = conn.cursor()
    c.execute("SELECT DISTINCT artist FROM albums ORDER BY artist")
    return [artist[0] for artist in c.fetchall()]

def fetch_tags(conn):
    """Fetch all unique tags from the tags table."""
    c = conn.cursor()
    c.execute("SELECT DISTINCT tag FROM tags ORDER BY tag")
    return [tag[0] for tag in c.fetchall()]

def fetch_albums_by_artist(conn, artist):
    """Fetch albums by the specified artist."""
    c = conn.cursor()
    c.execute("SELECT * FROM albums WHERE artist = ? ORDER BY release_date DESC", (artist,))
    return c.fetchall()

def fetch_albums_by_tag(conn, tag):
    """Fetch albums associated with the specified tag."""
    c = conn.cursor()
    c.execute('''
        SELECT albums.* FROM albums
        JOIN album_tags ON albums.id = album_tags.album_id
        JOIN tags ON tags.id = album_tags.tag_id
        WHERE tags.tag = ?
        ORDER BY albums.artist, albums.release_date DESC
    ''', (tag,))
    return c.fetchall()

def insert_album_data(conn, album_info, tags):
    """Insert new album data into the albums table and associate tags."""
    c = conn.cursor()
    # Check if the album already exists by URL to prevent duplicates
    c.execute('SELECT id FROM albums WHERE album_url = ?', (album_info['album_url'],))
    if c.fetchone():
        print("Album already exists in the database.")
        return

    c.execute('''
        INSERT INTO albums (artist, album_name, release_date, release_year, album_url)
        VALUES (:artist, :album_name, :release_date, :release_year, :album_url)
    ''', album_info)
    album_id = c.lastrowid

    for tag in tags:
        c.execute('INSERT OR IGNORE INTO tags (tag) VALUES (?)', (tag,))
        c.execute('SELECT id FROM tags WHERE tag = ?', (tag,))
        tag_id = c.fetchone()[0]
        c.execute('INSERT INTO album_tags (album_id, tag_id) VALUES (?, ?)', (album_id, tag_id))
    conn.commit()

def delete_album(conn, album_id):
    """Delete an album and clean up related tags and album_tags entries."""
    c = conn.cursor()
    c.execute("DELETE FROM album_tags WHERE album_id = ?", (album_id,))
    c.execute("DELETE FROM albums WHERE id = ?", (album_id,))
    c.execute("""
        DELETE FROM tags
        WHERE id NOT IN (
            SELECT DISTINCT tag_id FROM album_tags
        )
    """)
    conn.commit()

def close_connection(conn):
    """Close the connection to the database."""
    conn.close()
