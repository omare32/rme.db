import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
from datetime import datetime
import webbrowser

def get_band_name():
    root = tk.Tk()
    root.title('MusicBrainz Search')
    
    # Center the window
    window_width = 300
    window_height = 150
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')
    
    band_var = tk.StringVar()
    
    tk.Label(root, text='Enter band name:', pady=10).pack()
    entry = tk.Entry(root, textvariable=band_var, width=30)
    entry.pack(pady=5)
    
    def on_submit():
        root.quit()
    
    tk.Button(root, text='Search', command=on_submit).pack(pady=10)
    entry.focus()
    entry.bind('<Return>', lambda e: on_submit())
    
    root.mainloop()
    value = band_var.get()
    root.destroy()
    return value

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

def create_results_window(title):
    window = tk.Toplevel()
    window.title(title)
    window.geometry('800x600')
    
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

def search_band(band_name):
    try:
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
        window, tree = create_results_window(f'Artists matching "{band_name}"')
        
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
                albums_window, albums_tree = create_results_window(f'Albums by {artist_name}')
                
                # Configure columns
                albums_tree['columns'] = ('title', 'type', 'year')
                albums_tree.heading('title', text='Title')
                albums_tree.heading('type', text='Type')
                albums_tree.heading('year', text='Year')
                
                # Add albums to treeview
                for album in albums_data['release-groups']:
                    first_release_date = album.get('first-release-date', 'N/A')[:4]
                    albums_tree.insert('', tk.END, values=(
                        album.get('title', 'N/A'),
                        album.get('primary-type', 'N/A'),
                        first_release_date
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
    band_name = get_band_name()
    if band_name.strip():
        search_band(band_name)
    else:
        messagebox.showwarning('Warning', 'Please enter a band name to search.')
