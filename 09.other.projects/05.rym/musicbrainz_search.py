import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
from datetime import datetime
import webbrowser
import traceback
import sys
from base64 import b64encode
from spotify_config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

class MainWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('MusicBrainz Search')
        
        # Center the window
        window_width = 300
        window_height = 150
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # Create search frame
        self.band_var = tk.StringVar()
        
        tk.Label(self.window, text='Enter band name:', pady=10).pack()
        self.entry = tk.Entry(self.window, textvariable=self.band_var, width=30)
        self.entry.pack(pady=5)
        
        search_button = tk.Button(self.window, text='Search', command=self.search)
        search_button.pack(pady=10)
        
        # Bind enter key
        self.entry.bind('<Return>', lambda e: self.search())
        self.entry.focus()
    
    def search(self):
        band_name = self.band_var.get().strip()
        if band_name:
            print(f"Searching for: {band_name}")
            search_band(self.window, band_name)
            self.entry.delete(0, tk.END)  # Clear the entry
        else:
            messagebox.showwarning('Warning', 'Please enter a band name.')

class SpotifyAPI:
    def __init__(self):
        self.token = None
        self.get_token()
    
    def get_token(self):
        auth = b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers={'Authorization': f'Basic {auth}'},
            data={'grant_type': 'client_credentials'}
        )
        response.raise_for_status()
        self.token = response.json()['access_token']
    
    def search_artist(self, name):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(
            'https://api.spotify.com/v1/search',
            headers=headers,
            params={'q': name, 'type': 'artist', 'limit': 1}
        )
        response.raise_for_status()
        return response.json()
    
    def get_albums(self, artist_id):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(
            f'https://api.spotify.com/v1/artists/{artist_id}/albums',
            headers=headers,
            params={'include_groups': 'album,single', 'limit': 50}
        )
        response.raise_for_status()
        return response.json()

class MusicBrainzSearch:
    def __init__(self):
        self.headers = {
            'User-Agent': 'MusicSearchApp/1.0.0 (your@email.com)',
            'Accept': 'application/json'
        }
        self.base_url = 'https://musicbrainz.org/ws/2'
    
    def get_albums(self, artist_id):
        url = f'{self.base_url}/release-group'
        params = {
            'artist': artist_id,
            'fmt': 'json',
            'type': 'album|ep',
            'limit': 100
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

def create_results_window(parent, title):
    window = tk.Toplevel(parent)
    window.title(title)
    window.geometry('800x600')
    window.transient(parent)
    window.grab_set()
    
    # Create main frame
    main_frame = ttk.Frame(window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create treeview
    tree = ttk.Treeview(main_frame, show='headings')
    tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
    tree.configure(yscrollcommand=scrollbar.set)
    
    return window, tree

def search_band(parent, band_name):
    try:
        print(f"Searching for band: {band_name}")
        mb = MusicBrainzSearch()
        
        # Search for artists
        url = f'{mb.base_url}/artist'
        params = {
            'query': band_name,
            'fmt': 'json'
        }
        
        response = requests.get(url, headers=mb.headers, params=params)
        response.raise_for_status()
        artists_data = response.json()
        
        if not artists_data['artists']:
            messagebox.showinfo('No Results', f'No artists found for {band_name}')
            return
        
        # Create artists window
        window, tree = create_results_window(parent, f'Artists matching "{band_name}"')
        
        # Configure columns
        tree['columns'] = ('name', 'type', 'country', 'score')
        tree.heading('name', text='Name')
        tree.heading('type', text='Type')
        tree.heading('country', text='Country')
        tree.heading('score', text='Score')
        
        # Store artist IDs for later use
        artist_ids = {}
        
        # Add artists to treeview
        for artist in artists_data['artists']:
            artist_id = artist['id']
            artist_ids[artist['name']] = artist_id
            tree.insert('', tk.END, values=(
                artist.get('name', 'N/A'),
                artist.get('type', 'N/A'),
                artist.get('country', 'N/A'),
                artist.get('score', 'N/A')
            ))
        
        def on_artist_select(event):
            selection = tree.selection()
            if not selection:
                return
            
            item = tree.item(selection[0])
            artist_name = item['values'][0]
            artist_id = artist_ids[artist_name]
            
            try:
                # Get albums
                albums_data = mb.get_albums(artist_id)
                
                # Create albums window
                albums_window, albums_tree = create_results_window(parent, f'Albums by {artist_name}')
                
                # Configure columns
                albums_tree['columns'] = ('title', 'type', 'year', 'popularity')
                albums_tree.heading('title', text='Title')
                albums_tree.heading('type', text='Type')
                albums_tree.heading('year', text='Year')
                albums_tree.heading('popularity', text='Popularity')
                
                # Get Spotify data
                try:
                    spotify = SpotifyAPI()
                    spotify_artist = spotify.search_artist(artist_name)['artists']['items'][0]
                    spotify_albums = spotify.get_albums(spotify_artist['id'])
                    
                    # Create album name to popularity mapping
                    popularity_map = {}
                    for album in spotify_albums['items']:
                        popularity_map[album['name'].lower()] = album.get('popularity', 'N/A')
                except Exception as e:
                    print(f"Spotify error: {e}")
                    popularity_map = {}
                
                # Add albums to treeview
                for album in albums_data['release-groups']:
                    title = album.get('title', 'N/A')
                    first_release_date = album.get('first-release-date', 'N/A')[:4]
                    popularity = popularity_map.get(title.lower(), 'N/A')
                    
                    albums_tree.insert('', tk.END, values=(
                        title,
                        album.get('primary-type', 'N/A'),
                        first_release_date,
                        f"{popularity}/100" if popularity != 'N/A' else 'N/A'
                    ))
                
                # Save full data to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"albums_{artist_name.replace(' ', '_')}_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(albums_data, f, indent=2)
                
            except Exception as e:
                messagebox.showerror('Error', f'Failed to fetch albums: {str(e)}')
        
        # Bind double-click event
        tree.bind('<Double-1>', on_artist_select)
        
        # Add instructions label
        ttk.Label(window, text='Double-click an artist to view their albums').pack(pady=5)
        
    except Exception as e:
        messagebox.showerror('Error', f'An error occurred: {str(e)}')

if __name__ == '__main__':
    try:
        app = MainWindow()
        app.window.mainloop()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        messagebox.showerror('Error', f'An unexpected error occurred: {str(e)}')
