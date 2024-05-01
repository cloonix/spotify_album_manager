import tkinter as tk
from tkinter import ttk, messagebox  # Import messagebox here
from tkinter import simpledialog
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import re
import db_manager
import shutil
from datetime import datetime

load_dotenv()

class SpotifyManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify item Manager")
        self.setup_spotify_client()
        self.setup_gui()

    def setup_spotify_client(self):
        """Setup the Spotify API client."""
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def setup_gui(self):
        """Sets up the GUI components."""
        navigation_frame = ttk.Frame(self.root)
        navigation_frame.pack(fill="both", expand=True, side="top")
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, side="top")
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill="x", side="bottom")

        self.item_list = ttk.Treeview(list_frame, columns=("Delete", "ID", "Artist", "item Name", "Release Date", "Release Year", "URL"), show="headings")
        for col in ["Delete", "ID", "Artist", "item Name", "Release Date", "Release Year", "URL"]:
            self.item_list.heading(col, text=col)
        self.item_list.pack(side="left", fill="both", expand=True)
        self.item_list.bind("<1>", self.on_single_click)  # Bind left mouse click for delete
        self.item_list.bind("<Double-1>", self.on_double_click)  # Bind double click for opening URL

        # Genre Tree
        self.genres_tree = ttk.Treeview(navigation_frame, columns=["Genre"], show="headings")
        self.genres_tree.heading("Genre", text="Genre")
        self.genres_tree.pack(side="left", fill="both", expand=True)
        self.genres_tree.bind("<<TreeviewSelect>>", self.on_genre_select)

        # Artist Tree
        self.artist_tree = ttk.Treeview(navigation_frame, columns=["Artist"], show="headings")
        self.artist_tree.heading("Artist", text="Artist")
        self.artist_tree.pack(side="left", fill="both", expand=True)
        self.artist_tree.bind("<<TreeviewSelect>>", self.on_artist_select)

        # Type Tree
        self.type_tree = ttk.Treeview(navigation_frame, columns=["Type"], show="headings")
        self.type_tree.heading("Type", text="Type")
        self.type_tree.pack(side="left", fill="both", expand=True)
        self.type_tree.bind("<<TreeviewSelect>>", self.on_type_select)

        # Label and entry for item URL
        ttk.Label(input_frame, text="item URL:").pack(side="left", padx=(10, 2))
        self.url_entry = ttk.Entry(input_frame, width=50)
        self.url_entry.pack(side="left", padx=(2, 10))

        # Label and entry for Genre
        ttk.Label(input_frame, text="Genre:").pack(side="left", padx=(10, 2))
        self.genres_entry = ttk.Entry(input_frame, width=20)
        self.genres_entry.pack(side="left", padx=(2, 10))

        add_button = ttk.Button(input_frame, text="Add item", command=self.add_item)
        add_button.pack(side="left")

        add_button = ttk.Button(input_frame, text="Close", command=self.close_application)
        add_button.pack(side="right")

        backup_button = ttk.Button(input_frame, text="Back Up", command=self.backup_database)
        backup_button.pack(side="right")  # Adjust placement as needed

        load_button = ttk.Button(input_frame, text="Load", command=self.choose_backup)
        load_button.pack(side="right")

        self.populate_artist_tree()
        self.populate_genres_tree()
        self.populate_type_tree()

    def populate_artist_tree(self):
        """Populates the artist tree with artist names."""
        self.artist_tree.delete(*self.artist_tree.get_children())  # Clear existing entries
        artists = db_manager.fetch_artists(conn)  # Fetch unique artists
        for artist in artists:
            self.artist_tree.insert('', 'end', text=artist, values=(artist,))

    def populate_type_tree(self):
        """Populates the type tree."""
        self.type_tree.delete(*self.type_tree.get_children())  # Clear existing entries
        types = db_manager.fetch_types(conn)  # Fetch unique types
        for type in types:
            self.type_tree.insert('', 'end', text=type, values=(type,))

    def populate_genres_tree(self):
        """Populates the genres tree with genres."""
        self.genres_tree.delete(*self.genres_tree.get_children())  # Clear existing entries
        genres = db_manager.fetch_genres(conn)  # Fetch unique genres
        for genre in genres:
            self.genres_tree.insert('', 'end', text=genre, values=(genre,))

    def on_artist_select(self, event):
        """Updates the item list based on selected artist."""
        selected_artist = self.artist_tree.item(self.artist_tree.selection())['values'][0]
        items = db_manager.fetch_items_by_artist(conn, selected_artist)
        self.update_item_list(items)

    def on_genre_select(self, event):
        """Updates the item list based on selected genre."""
        selected_genre = self.genres_tree.item(self.genres_tree.selection())['values'][0]
        items = db_manager.fetch_items_by_genre(conn, selected_genre)
        self.update_item_list(items)

    def on_type_select(self, event):
        """Updates the type list based on selected type."""
        selected_type = self.type_tree.item(self.type_tree.selection())['values'][0]
        items = db_manager.fetch_items_by_type(conn, selected_type)
        self.update_item_list(items)

    def open_url(self, item_id):
        """Open the item URL from the list."""
        item = self.item_list.item(item_id)
        url = item['values'][6]  # Assuming URL is in the last column
        webbrowser.open(url)

    def update_item_list(self, items):
        """Update the item list view with the given items."""
        self.item_list.delete(*self.item_list.get_children())
        for item in items:
            # Adding a trash bin icon or text in the first column for deletion
            self.item_list.insert('', 'end', values=("🗑️",) + item)

    def get_spotify_type_and_id(self, url):
        pattern = r"open\.spotify\.com\/(album|track)\/([a-zA-Z0-9]+)"
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def fetch_item_info(self, url):
        item_type, item_id = self.get_spotify_type_and_id(url)
        if item_type == "album":
            item_data = self.sp.album(item_id)
        elif item_type == "track":
            item_data = self.sp.track(item_id)
        else:
            return None  # Handle error or invalid URL
        return item_data

    def add_item(self):
        url = self.url_entry.get()
        genres = self.genres_entry.get().split(',')
        item_info = self.fetch_item_info(url)
        if item_info:
            # Create a dictionary to insert into the database
            item_data = {
                'artist': item_info['artists'][0]['name'],
                'item_name': item_info['name'],
                'release_date': item_info.get('release_date', ''),
                'release_year': item_info.get('release_date', '')[:4],
                'item_url': url,
                'type': item_info['type']
            }
            db_manager.insert_item_data(conn, item_data, genres)
            self.refresh_views()
        else:
            print("Failed to fetch item info")

    def refresh_views(self):
        """Refresh all GUI views to display current database contents."""
        self.populate_artist_tree()
        self.populate_genres_tree()
        items = db_manager.fetch_items(conn)  # Make sure this method exists in db_manager
        self.update_item_list(items)

    def on_single_click(self, event):
        """Handle single clicks, specifically check if the delete icon was clicked."""
        region = self.item_list.identify("region", event.x, event.y)
        if region == "cell":
            column = self.item_list.identify_column(event.x)
            if column == "#1":  # Check if the delete column was clicked
                item_id = self.item_list.identify_row(event.y)
                self.confirm_delete(item_id)

    def on_double_click(self, event):
        """Handle double-click events to open URLs."""
        region = self.item_list.identify("region", event.x, event.y)
        if region == "cell":
            column = self.item_list.identify_column(event.x)
            if column != "#1":  # Ensure the click is not on the delete icon
                item_id = self.item_list.identify_row(event.y)
                self.open_url(item_id)

    def confirm_delete(self, item_id):
        """Confirm deletion of an item."""
        item = self.item_list.item(item_id)
        item_id = item['values'][1]  # Assuming ID is in the second column
        response = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?")
        if response:
            db_manager.delete_item(conn, item_id)
            self.refresh_views()

    def list_backups(self):
        files = [f for f in os.listdir() if f.startswith('items_') and f.endswith('.db')]
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)  # Sort by most recent
        return files[:3]  # Return the last three backups

    def backup_database(self):
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
        source_db = 'collection.db'  # Assuming this is the name and path of your main database file
        backup_db = f'items_{current_time}.db'  # Backup file name with timestamp
        shutil.copy(source_db, backup_db)  # Copy the source database to the new backup file
        print(f"Backup created: {backup_db}")  # Optional: Print confirmation to the console

    def choose_backup(self):
        backups = self.list_backups()  # Get the list of backups
        if not backups:
            messagebox.showinfo("Error", "No backup files found.")
            return

        # Create a new Toplevel window
        win = tk.Toplevel()
        win.wm_title("Load Backup")

        # Create a label
        label = ttk.Label(win, text="Choose a backup:")
        label.pack(padx=10, pady=10)

        # Create a Combobox for backups
        backup_var = tk.StringVar(win)
        backup_combo = ttk.Combobox(win, textvariable=backup_var, values=backups)
        backup_combo.pack(padx=10, pady=10)
        backup_combo.set(backups[0])  # Set default selection to the first backup

        # Function to load the selected backup
        def on_ok():
            backup_file = backup_var.get()
            if backup_file:
                self.load_backup(backup_file)  # Load the selected backup
                win.destroy()  # Close the window after loading the backup

        # Add a "Load" button
        load_button = ttk.Button(win, text="Load", command=on_ok)
        load_button.pack(pady=(0, 10))

        # Add a "Cancel" button
        cancel_button = ttk.Button(win, text="Cancel", command=win.destroy)
        cancel_button.pack(pady=(0, 10))

    def load_backup(self, backup_file):
        shutil.copy(backup_file, 'collection.db')  # Replace the current database with the backup
        self.reload_gui_content()  # Reload the GUI content

    def reload_gui_content(self):
        # Code to refresh the data displayed in the GUI
        # This depends on how your GUI is set up to display data from the database
        app.refresh_views()

    def close_application(self):
        self.root.destroy()  # This will close the Tkinter application window

if __name__ == "__main__":
    conn = db_manager.create_connection()
    root = tk.Tk()
    app = SpotifyManagerGUI(root)
    app.refresh_views()
    root.mainloop()
    db_manager.close_connection(conn)
