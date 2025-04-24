#!/usr/bin/env python3
import os
import glob
import json
import time
import shutil
import logging
import re
from datetime import datetime
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from moviepy.editor import VideoFileClip, concatenate_videoclips
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# OAuth 2.0 credentials
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS_FILE = "client_secrets.json"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_merge.log'),
        logging.StreamHandler()
    ]
)

class ProgressWindow:
    def __init__(self, title):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("400x150")
        
        # Center the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 150) // 2
        self.root.geometry(f"400x150+{x}+{y}")
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.root, orient="horizontal", length=300, mode="determinate"
        )
        self.progress.pack(pady=20)
        
        # Status label
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = tk.Label(self.root, textvariable=self.status_var)
        self.status_label.pack(pady=10)
        
        # Time remaining label
        self.time_var = tk.StringVar(value="")
        self.time_label = tk.Label(self.root, textvariable=self.time_var)
        self.time_label.pack(pady=5)
        
        self.start_time = time.time()
        
    def update_progress(self, current: float, total: float, status: str = None):
        """Update progress bar and status."""
        if not self.root:
            return
            
        progress = (current / total) * 100
        self.progress["value"] = progress
        
        if status:
            self.status_var.set(status)
            
        # Calculate and show estimated time remaining
        if progress > 0:
            elapsed = time.time() - self.start_time
            total_time = elapsed * (100 / progress)
            remaining = total_time - elapsed
            
            if remaining > 60:
                time_str = f"Estimated time remaining: {remaining/60:.1f} minutes"
            else:
                time_str = f"Estimated time remaining: {remaining:.0f} seconds"
                
            self.time_var.set(time_str)
            
        self.root.update()
        
    def close(self):
        """Close the progress window."""
        if self.root:
            self.root.destroy()
            self.root = None

class VideoMergerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Video Merger & YouTube Uploader")
        self.root.geometry("800x600")
        
        # Center the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 600) // 2
        self.root.geometry(f"800x600+{x}+{y}")
        
        self.create_widgets()
        self.selected_files = []
        self.output_path = None
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Source folder selection
        ttk.Label(main_frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.source_path = tk.StringVar()
        source_entry = ttk.Entry(main_frame, textvariable=self.source_path, width=60)
        source_entry.grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_source).grid(row=0, column=2)
        
        # Files listbox
        ttk.Label(main_frame, text="Available Videos:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.files_listbox = tk.Listbox(main_frame, width=70, height=15, selectmode=tk.MULTIPLE)
        self.files_listbox.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # Scrollbar for listbox
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        scrollbar.grid(row=2, column=3, sticky=(tk.N, tk.S))
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Output path selection
        ttk.Label(main_frame, text="Output Folder:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.output_folder = tk.StringVar()
        output_entry = ttk.Entry(main_frame, textvariable=self.output_folder, width=60)
        output_entry.grid(row=3, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(row=3, column=2)
        
        # YouTube upload options
        youtube_frame = ttk.LabelFrame(main_frame, text="YouTube Upload Options", padding="5")
        youtube_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(youtube_frame, text="Title:").grid(row=0, column=0, sticky=tk.W)
        self.video_title = tk.StringVar()
        ttk.Entry(youtube_frame, textvariable=self.video_title, width=60).grid(row=0, column=1, padx=5)
        
        ttk.Label(youtube_frame, text="Description:").grid(row=1, column=0, sticky=tk.W)
        self.video_desc = tk.Text(youtube_frame, width=45, height=3)
        self.video_desc.grid(row=1, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Merge Videos", command=self.merge_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Upload to YouTube", command=self.upload_to_youtube).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
    def browse_source(self):
        folder = filedialog.askdirectory(
            initialdir="\\\\fileserver2\\Head Office Server\\Projects Control (PC)\\10 Backup\\05 Tutorials\\Google\\Maps-Test",
            title="Select Source Folder"
        )
        if folder:
            self.source_path.set(folder)
            self.update_file_list()
            
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
            
    def update_file_list(self):
        self.files_listbox.delete(0, tk.END)
        folder = self.source_path.get()
        if folder:
            for file in sorted(glob.glob(os.path.join(folder, "**/*.mp4"), recursive=True)):
                self.files_listbox.insert(tk.END, os.path.relpath(file, folder))
                
    def merge_selected(self):
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select videos to merge")
            return
            
        if not self.output_folder.get():
            messagebox.showwarning("Warning", "Please select output folder")
            return
            
        # Get selected files
        source_folder = self.source_path.get()
        video_files = []
        for idx in selected_indices:
            filename = self.files_listbox.get(idx)
            full_path = os.path.join(source_folder, filename)
            video_files.append((full_path, filename))
            
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_folder.get(), f"merged_{timestamp}.mp4")
        self.output_path = output_path
        
        # Start merge in a separate thread
        thread = threading.Thread(target=self._merge_thread, args=(video_files, output_path))
        thread.start()
        
    def _merge_thread(self, video_files: List[Tuple[str, str]], output_path: str):
        if merge_videos(video_files, output_path):
            self.root.after(0, lambda: messagebox.showinfo("Success", 
                f"Videos merged successfully!\nSaved to: {output_path}"))
        else:
            self.root.after(0, lambda: messagebox.showerror("Error", 
                "Failed to merge videos. Check the log file for details."))
                
    def get_credentials(self):
        creds = None
        if os.path.exists('token.json'):
            try:
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            except Exception:
                pass
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                
        return creds
        
    def upload_to_youtube(self):
        if not self.output_path or not os.path.exists(self.output_path):
            messagebox.showwarning("Warning", "Please merge videos first")
            return
            
        if not os.path.exists(CLIENT_SECRETS_FILE):
            messagebox.showerror("Error", 
                f"Missing {CLIENT_SECRETS_FILE}. Please obtain it from Google Cloud Console.")
            return
            
        title = self.video_title.get()
        description = self.video_desc.get("1.0", tk.END).strip()
        
        if not title:
            messagebox.showwarning("Warning", "Please enter a video title")
            return
            
        # Start upload in a separate thread
        thread = threading.Thread(target=self._upload_thread, args=(title, description))
        thread.start()
        
    def _upload_thread(self, title: str, description: str):
        try:
            creds = self.get_credentials()
            youtube = build('youtube', 'v3', credentials=creds)
            
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': 'private'
                }
            }
            
            insert_request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=MediaFileUpload(
                    self.output_path,
                    chunksize=-1,
                    resumable=True
                )
            )
            
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    self.root.after(0, lambda: messagebox.showinfo("Upload Status", 
                        f"Upload is {int(status.progress() * 100)}% complete..."))
                    
            self.root.after(0, lambda: messagebox.showinfo("Success", 
                f"Upload Complete!\nVideo ID: {response['id']}"))
                
        except HttpError as e:
            self.root.after(0, lambda: messagebox.showerror("Error", 
                f"An HTTP error occurred: {e.resp.status} {e.content}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", 
                f"An error occurred: {str(e)}"))

def videos_are_compatible(video_paths: List[str]) -> bool:
    """Check if videos can be directly concatenated."""
    if not video_paths:
        return False
        
    try:
        # Get video info using ffprobe
        def get_video_info(path):
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=codec_name,width,height,r_frame_rate',
                '-of', 'json',
                path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return json.loads(result.stdout)
            
        # Get first video's properties
        base_info = get_video_info(video_paths[0])
        base_stream = base_info['streams'][0]
        
        # Check all other videos
        for path in video_paths[1:]:
            info = get_video_info(path)
            stream = info['streams'][0]
            
            # Compare properties
            if (stream['codec_name'] != base_stream['codec_name'] or
                stream['width'] != base_stream['width'] or
                stream['height'] != base_stream['height'] or
                stream['r_frame_rate'] != base_stream['r_frame_rate']):
                return False
                
        return True
        
    except Exception as e:
        logging.error(f"Error checking video compatibility: {str(e)}")
        return False

def direct_concatenate(video_paths: List[str], output_path: str, progress_window) -> bool:
    """Merge videos using direct binary concatenation."""
    try:
        # Calculate total size for progress tracking
        total_size = sum(os.path.getsize(path) for path in video_paths)
        current_size = 0
        
        with open(output_path, 'wb') as outfile:
            for path in video_paths:
                # Update status
                filename = os.path.basename(path)
                progress_window.update_progress(
                    current_size,
                    total_size,
                    f"Processing {filename}..."
                )
                
                # Copy file in chunks
                with open(path, 'rb') as infile:
                    while True:
                        chunk = infile.read(1024*1024)  # 1MB chunks
                        if not chunk:
                            break
                        outfile.write(chunk)
                        current_size += len(chunk)
                        progress_window.update_progress(current_size, total_size)
                        
        return True
        
    except Exception as e:
        logging.error(f"Error in direct concatenation: {str(e)}")
        return False

def merge_with_moviepy(video_paths: List[str], output_path: str, progress_window) -> bool:
    """Merge videos using MoviePy."""
    clips = []
    total_duration = 0
    
    try:
        # First pass: load clips and calculate total duration
        for path in video_paths:
            filename = os.path.basename(path)
            progress_window.update_progress(
                0, 1,
                f"Loading {filename}..."
            )
            clip = VideoFileClip(path)
            clips.append(clip)
            total_duration += clip.duration
            
        # Second pass: concatenate and write
        final_clip = concatenate_videoclips(clips)
        
        def progress_callback(t):
            progress_window.update_progress(
                t,
                total_duration,
                "Writing merged video..."
            )
            
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            progress_bar=False,
            callback=progress_callback
        )
        
        return True
        
    except Exception as e:
        logging.error(f"Error in MoviePy merge: {str(e)}")
        return False
        
    finally:
        # Clean up clips
        for clip in clips:
            try:
                clip.close()
            except:
                pass

def merge_videos(video_files: List[Tuple[str, str]], output_path: str) -> bool:
    """
    Merge a list of videos into a single file.
    
    Args:
        video_files: List of tuples (file_path, file_name)
        output_path: Path where the merged video will be saved
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract just the file paths
        video_paths = [path for path, _ in video_files]
        
        if not video_paths:
            logging.error("No video files provided")
            return False
            
        # Create progress window
        progress_window = ProgressWindow("Merging Videos")
        
        # Check if videos are compatible for direct concatenation
        progress_window.update_progress(0, 1, status="Checking video compatibility...")
        if videos_are_compatible(video_paths):
            logging.info("Videos are compatible - using direct concatenation")
            progress_window.update_progress(0, 1, status="Starting direct concatenation...")
            success = direct_concatenate(video_paths, output_path, progress_window)
            progress_window.close()
            return success
            
        # If not compatible, use MoviePy
        logging.info("Videos are not compatible - using MoviePy")
        progress_window.update_progress(0, 1, status="Starting MoviePy merge...")
        success = merge_with_moviepy(video_paths, output_path, progress_window)
        progress_window.close()
        return success
        
    except Exception as e:
        logging.error(f"Error in merge_videos: {str(e)}")
        return False

def test_merge():
    """Test function to try out video merging."""
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Look for MP4 files in the current directory
    video_files = []
    for file in sorted(glob.glob(os.path.join(current_dir, "*.mp4"))):
        # Create tuple of (full_path, filename)
        video_files.append((file, os.path.basename(file)))
    
    if not video_files:
        print("No MP4 files found in the current directory")
        return
    
    print(f"Found {len(video_files)} MP4 files:")
    for _, filename in video_files:
        print(f"- {filename}")
    
    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(current_dir, f"merged_{timestamp}.mp4")
    
    print(f"\nAttempting to merge videos into: {output_path}")
    if merge_videos(video_files, output_path):
        print(f"\nSuccess! Merged video saved to: {output_path}")
    else:
        print("\nError: Video merge failed. Check the log file for details.")

if __name__ == "__main__":
    app = VideoMergerApp()
    app.root.mainloop()