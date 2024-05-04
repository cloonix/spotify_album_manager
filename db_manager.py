import sqlite3

def create_connection(db_file='collection.db'):
    """Create and return a database connection and ensure tables are created."""
    conn = sqlite3.connect(db_file)  # This will create the database file if it doesn't exist
    create_tables(conn)  # Create tables if not already present
    return conn

def create_tables(conn):
    """Create the tables required for the application."""
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist TEXT NOT NULL,
            item_name TEXT NOT NULL,
            release_date TEXT,
            release_year INTEGER,
            item_url TEXT UNIQUE,
            type
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            genre TEXT UNIQUE NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS item_genres (
            item_id INTEGER,
            genre_id INTEGER,
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE,
            UNIQUE(item_id, genre_id)
        )
    ''')
    conn.commit()

def fetch_items(conn):
    """Fetch all items sorted by artist name."""
    c = conn.cursor()
    # Ensure the order here matches what is expected in your GUI
    c.execute("SELECT id, artist, item_name, release_date, release_year, item_url, type FROM items ORDER BY artist")
    return c.fetchall()

def fetch_artists(conn):
    """Fetch all unique artists from the items table."""
    c = conn.cursor()
    c.execute("SELECT DISTINCT artist FROM items ORDER BY artist")
    return [artist[0] for artist in c.fetchall()]

def fetch_genres(conn):
    """Fetch all unique genres from the genres table."""
    c = conn.cursor()
    c.execute("SELECT DISTINCT genre FROM genres ORDER BY genre")
    return [genre[0] for genre in c.fetchall()]

def fetch_types(conn):
    """Fetch all types."""
    c = conn.cursor()
    c.execute("SELECT DISTINCT type FROM items")
    return [type[0] for type in c.fetchall()]

def fetch_items_by_artist(conn, artist):
    """Fetch items by the specified artist."""
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE artist = ? ORDER BY release_date DESC", (artist,))
    return c.fetchall()

def fetch_items_by_genre(conn, genre):
    """Fetch items associated with the specified genre."""
    c = conn.cursor()
    c.execute('''
        SELECT items.* FROM items
        JOIN item_genres ON items.id = item_genres.item_id
        JOIN genres ON genres.id = item_genres.genre_id
        WHERE genres.genre = ?
        ORDER BY items.artist, items.release_date DESC
    ''', (genre,))
    return c.fetchall()

def fetch_artists_by_genre(conn, genre):
    """Fetch all unique artists associated with the specified genre."""
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT items.artist FROM items
        JOIN item_genres ON items.id = item_genres.item_id
        JOIN genres ON genres.id = item_genres.genre_id
        WHERE genres.genre = ?
        ORDER BY items.artist
    ''', (genre,))
    return [artist[0] for artist in c.fetchall()]

def fetch_items_by_type(conn, type_name):
    """ Fetch items from the database filtered by type. """
    c = conn.cursor()
    c.execute('''
        SELECT items.* FROM items
        WHERE type = ?
    ''', (type_name,))
    return c.fetchall()

def fetch_types_by_artist(conn, artist):
    """Fetch all unique item types associated with the specified artist."""
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT type FROM items
        WHERE artist = ?
        ORDER BY type
    ''', (artist,))
    return [type[0] for type in c.fetchall()]

def insert_item_data(conn, item_info, genres):
    """Insert new item data into the items table and associate genres."""
    c = conn.cursor()
    # Check if the item already exists by URL to prevent duplicates
    c.execute('SELECT id FROM items WHERE item_url = ?', (item_info['item_url'],))
    if c.fetchone():
        print("item already exists in the database.")
        return

    c.execute('''
        INSERT INTO items (artist, item_name, release_date, release_year, item_url, type)
        VALUES (:artist, :item_name, :release_date, :release_year, :item_url, :type)
    ''', item_info)
    item_id = c.lastrowid

    for genre in genres:
        c.execute('INSERT OR IGNORE INTO genres (genre) VALUES (?)', (genre,))
        c.execute('SELECT id FROM genres WHERE genre = ?', (genre,))
        genre_id = c.fetchone()[0]
        c.execute('INSERT INTO item_genres (item_id, genre_id) VALUES (?, ?)', (item_id, genre_id))
    conn.commit()

def delete_item(conn, item_id):
    """Delete an item and clean up related genres and item_genres entries."""
    c = conn.cursor()
    c.execute("DELETE FROM item_genres WHERE item_id = ?", (item_id,))
    c.execute("DELETE FROM items WHERE id = ?", (item_id,))
    c.execute("""
        DELETE FROM genres
        WHERE id NOT IN (
            SELECT DISTINCT genre_id FROM item_genres
        )
    """)
    conn.commit()

def close_connection(conn):
    """Close the connection to the database."""
    conn.close()
