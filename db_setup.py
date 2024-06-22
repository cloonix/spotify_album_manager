def create_tables(conn):
    """Create the tables required for the application."""
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist TEXT NOT NULL,
            item_name TEXT NOT NULL,
            release_date TEXT,
            release_year INTEGER,
            item_url TEXT UNIQUE,
            type
        )
    """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            genre TEXT UNIQUE NOT NULL
        )
    """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS item_genres (
            item_id INTEGER,
            genre_id INTEGER,
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE,
            UNIQUE(item_id, genre_id)
        )
    """
    )
    conn.commit()
