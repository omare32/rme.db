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
from typing import List, Dict, Optional, Tuple, Union
import tkinter as tk
from tkinter import ttk, messagebox
from moviepy.editor import VideoFileClip, concatenate_videoclips
import cv2
import numpy as np
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_merge.log'),
        logging.StreamHandler()
    ]
)

TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class ProgressWindow:
    def __init__(self, title="Progress", parent=None):
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title(title)
        self.root.geometry("600x200")
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack(pady=(0, 5))
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            variable=self.progress_var,
            maximum=100,
            length=500
        )
        self.progress_bar.pack(pady=5)
        
        # Details frame
        details_frame = ttk.LabelFrame(main_frame, text="Details", padding="5")
        details_frame.pack(fill=tk.X, pady=5)
        
        # Time info
        time_frame = ttk.Frame(details_frame)
        time_frame.pack(fill=tk.X, pady=2)
        
        self.elapsed_var = tk.StringVar(value="Elapsed: 0:00:00")
        self.remaining_var = tk.StringVar(value="Remaining: --:--:--")
        
        ttk.Label(time_frame, textvariable=self.elapsed_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, textvariable=self.remaining_var).pack(side=tk.RIGHT, padx=5)
        
        # Stats frame
        stats_frame = ttk.Frame(details_frame)
        stats_frame.pack(fill=tk.X, pady=2)
        
        self.speed_var = tk.StringVar(value="Speed: --")
        self.size_var = tk.StringVar(value="Size: --")
        
        ttk.Label(stats_frame, textvariable=self.speed_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(stats_frame, textvariable=self.size_var).pack(side=tk.RIGHT, padx=5)
        
        self.start_time = time.time()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.allow_close = False

    def on_closing(self):
        if self.allow_close:
            self.root.destroy()

    def update_progress(self, current: float, total: float, 
                       speed: str = "", size: str = "", status: str = None):
        if status:
            self.status_var.set(status)
        
        progress = (current / total * 100) if total > 0 else 0
        self.progress_var.set(progress)
        
        elapsed = time.time() - self.start_time
        elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
        self.elapsed_var.set(f"Elapsed: {elapsed_str}")
        
        if progress > 0:
            total_estimated = elapsed / (progress / 100)
            remaining = total_estimated - elapsed
            remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining))
            self.remaining_var.set(f"Remaining: {remaining_str}")
        
        if speed:
            self.speed_var.set(f"Speed: {speed}")
        if size:
            self.size_var.set(f"Size: {size}")
        
        self.root.update()

    def close(self):
        self.allow_close = True
        self.root.destroy()

def get_video_info(video_path: str) -> Optional[Dict]:
    """Get video information using OpenCV."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
            
        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fourcc': int(cap.get(cv2.CAP_PROP_FOURCC)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))
        }
        cap.release()
        return info
    except Exception as e:
        logging.error(f"Error getting video info: {str(e)}")
        return None

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
    test_merge()

[... Rest of the code from rev.08 remains the same ...] 