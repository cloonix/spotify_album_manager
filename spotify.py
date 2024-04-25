import tkinter as tk
from tkinter import ttk, messagebox  # Import messagebox here
from tkinter import simpledialog
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import db_manager
import shutil
from datetime import datetime

load_dotenv()

class SpotifyManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Album Manager")
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
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, side="top")
        navigation_frame = ttk.Frame(self.root)
        navigation_frame.pack(fill="both", expand=True, side="top")
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill="x", side="bottom")

        self.album_list = ttk.Treeview(list_frame, columns=("Delete", "ID", "Artist", "Album Name", "Release Date", "Release Year", "URL"), show="headings")
        for col in ["Delete", "ID", "Artist", "Album Name", "Release Date", "Release Year", "URL"]:
            self.album_list.heading(col, text=col)
        self.album_list.pack(side="left", fill="both", expand=True)
        self.album_list.bind("<1>", self.on_single_click)  # Bind left mouse click for delete
        self.album_list.bind("<Double-1>", self.on_double_click)  # Bind double click for opening URL

        # Artist Tree
        self.artist_tree = ttk.Treeview(navigation_frame, columns=["Artist"], show="headings")
        self.artist_tree.heading("Artist", text="Artist")
        self.artist_tree.pack(side="left", fill="both", expand=True)
        self.artist_tree.bind("<<TreeviewSelect>>", self.on_artist_select)

        # Tags Tree
        self.tags_tree = ttk.Treeview(navigation_frame, columns=["Tag"], show="headings")
        self.tags_tree.heading("Tag", text="Tag")
        self.tags_tree.pack(side="left", fill="both", expand=True)
        self.tags_tree.bind("<<TreeviewSelect>>", self.on_tag_select)

        # Label and entry for Album URL
        ttk.Label(input_frame, text="Album URL:").pack(side="left", padx=(10, 2))
        self.url_entry = ttk.Entry(input_frame, width=50)
        self.url_entry.pack(side="left", padx=(2, 10))

        # Label and entry for Tags
        ttk.Label(input_frame, text="Tags:").pack(side="left", padx=(10, 2))
        self.tags_entry = ttk.Entry(input_frame, width=20)
        self.tags_entry.pack(side="left", padx=(2, 10))

        add_button = ttk.Button(input_frame, text="Add Album", command=self.add_album)
        add_button.pack(side="left")

        add_button = ttk.Button(input_frame, text="Close", command=self.close_application)
        add_button.pack(side="right")

        backup_button = ttk.Button(input_frame, text="Back Up", command=self.backup_database)
        backup_button.pack(side="right")  # Adjust placement as needed

        load_button = ttk.Button(input_frame, text="Load", command=self.choose_backup)
        load_button.pack(side="right")

        self.populate_artist_tree()
        self.populate_tags_tree()

    def populate_artist_tree(self):
        """Populates the artist tree with artist names."""
        self.artist_tree.delete(*self.artist_tree.get_children())  # Clear existing entries
        artists = db_manager.fetch_artists(conn)  # Fetch unique artists
        for artist in artists:
            self.artist_tree.insert('', 'end', text=artist, values=(artist,))

    def populate_tags_tree(self):
        """Populates the tags tree with tags."""
        self.tags_tree.delete(*self.tags_tree.get_children())  # Clear existing entries
        tags = db_manager.fetch_tags(conn)  # Fetch unique tags
        for tag in tags:
            self.tags_tree.insert('', 'end', text=tag, values=(tag,))

    def on_artist_select(self):
        """Updates the album list based on selected artist."""
        selected_artist = self.artist_tree.item(self.artist_tree.selection())['values'][0]
        albums = db_manager.fetch_albums_by_artist(conn, selected_artist)
        self.update_album_list(albums)

    def on_tag_select(self):
        """Updates the album list based on selected tag."""
        selected_tag = self.tags_tree.item(self.tags_tree.selection())['values'][0]
        albums = db_manager.fetch_albums_by_tag(conn, selected_tag)
        self.update_album_list(albums)

    def open_url(self, item_id):
        """Open the album URL from the list."""
        item = self.album_list.item(item_id)
        url = item['values'][6]  # Assuming URL is in the last column
        webbrowser.open(url)

    def update_album_list(self, albums):
        """Update the album list view with the given albums."""
        self.album_list.delete(*self.album_list.get_children())
        for album in albums:
            # Adding a trash bin icon or text in the first column for deletion
            self.album_list.insert('', 'end', values=("🗑️",) + album)

    def fetch_album_info(self, album_url):
        """Fetch album information from Spotify based on the URL."""
        album_id = album_url.split("/")[-1].split("?")[0]
        album_data = self.sp.album(album_id)
        release_year = album_data['release_date'].split("-")[0]
        return {
            "artist": album_data['artists'][0]['name'],
            "album_name": album_data['name'],
            "release_date": album_data['release_date'],
            "release_year": int(release_year),
            "album_url": album_url
        }

    def add_album(self):
        """Add a new album from the URL and tags provided by the user."""
        url = self.url_entry.get()
        tags = self.tags_entry.get().split(',')
        album_info = self.fetch_album_info(url)
        db_manager.insert_album_data(conn, album_info, tags)
        self.refresh_views()

    def refresh_views(self):
        """Refresh all GUI views to display current database contents."""
        self.populate_artist_tree()
        self.populate_tags_tree()
        albums = db_manager.fetch_albums(conn)  # Make sure this method exists in db_manager
        self.update_album_list(albums)

    def on_single_click(self, event):
        """Handle single clicks, specifically check if the delete icon was clicked."""
        region = self.album_list.identify("region", event.x, event.y)
        if region == "cell":
            column = self.album_list.identify_column(event.x)
            if column == "#1":  # Check if the delete column was clicked
                item_id = self.album_list.identify_row(event.y)
                self.confirm_delete(item_id)

    def on_double_click(self, event):
        """Handle double-click events to open URLs."""
        region = self.album_list.identify("region", event.x, event.y)
        if region == "cell":
            column = self.album_list.identify_column(event.x)
            if column != "#1":  # Ensure the click is not on the delete icon
                item_id = self.album_list.identify_row(event.y)
                self.open_url(item_id)

    def confirm_delete(self, item_id):
        """Confirm deletion of an album."""
        item = self.album_list.item(item_id)
        album_id = item['values'][1]  # Assuming ID is in the second column
        response = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this album?")
        if response:
            db_manager.delete_album(conn, album_id)
            self.refresh_views()

    def list_backups(self):
        files = [f for f in os.listdir() if f.startswith('albums_') and f.endswith('.db')]
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)  # Sort by most recent
        return files[:3]  # Return the last three backups

    def backup_database(self):
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
        source_db = 'albums.db'  # Assuming this is the name and path of your main database file
        backup_db = f'albums_{current_time}.db'  # Backup file name with timestamp
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
        shutil.copy(backup_file, 'albums.db')  # Replace the current database with the backup
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
