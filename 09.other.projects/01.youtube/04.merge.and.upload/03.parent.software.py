import os
import subprocess
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import mysql.connector as mysql
import pandas as pd
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime
from openpyxl.utils import get_column_letter
import tkinter as tk
from tkinter import simpledialog, messagebox
from googleapiclient.errors import HttpError, ResumableUploadError
import json
from datetime import datetime, timedelta
import time
import httplib2
import socket
import urllib3
from googleapiclient.http import build_http

# Disable SSL verification
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Google API configuration
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = os.path.join(SCRIPT_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")
YOUTUBE_MAX_DURATION = 43200  # 12 hours in seconds
QUOTA_STATE_FILE = os.path.join(SCRIPT_DIR, "quota_state.json")
MAX_RETRIES = 3
RETRY_DELAY = 3600  # 1 hour in seconds

MERGE_TIMEOUT = 4800  # 80 minutes
CONVERT_TIMEOUT = 7200  # 2 hours

def save_quota_state(reset_time):
    """Save the quota reset time to a file"""
    with open(QUOTA_STATE_FILE, 'w') as f:
        json.dump({'reset_time': reset_time.isoformat()}, f)

def get_quota_state():
    """Get the saved quota state"""
    try:
        with open(QUOTA_STATE_FILE, 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data['reset_time'])
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None

def handle_quota_error():
    """Handle quota exceeded error by saving state and suggesting wait time"""
    # Set reset time to next day at midnight UTC
    reset_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    save_quota_state(reset_time)
    wait_time = (reset_time - datetime.utcnow()).total_seconds()
    return reset_time, wait_time

def get_authenticated_service():
    """
    Authenticate with YouTube API and return a service object.
    If re-authentication is required, open a browser before starting the process.
    """
    # Disable SSL verification warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    creds = None

    # ✅ Check if a token file exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # ✅ If token is missing or invalid, refresh or re-authenticate before merging starts
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("🔄 Token expired. Attempting to refresh...")
                creds.refresh(Request())
                print("✅ Token refreshed successfully!")
            except Exception as e:
                print(f"⚠️ Token refresh failed: {e}\n🌐 Opening browser for re-authentication...")
                creds = None  # Force re-authentication

        if creds is None:
            print("🌐 Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            # Use local_server with SSL verification disabled
            creds = flow.run_local_server(port=0, ssl_verify=False)

        # ✅ Save the new token immediately
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    # Create service with the credentials
    return build("youtube", "v3", credentials=creds)

def get_all_video_files(folder_path):
    """
    Recursively get all video files from a folder and its subfolders.
    Returns a sorted list of video files with their full paths and relative paths for timestamps.
    """
    video_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                full_path = os.path.join(root, file)
                # Get the relative path from the parent folder for timestamps
                rel_path = os.path.relpath(full_path, folder_path)
                video_files.append((rel_path, full_path))
    
    # Sort by relative path to maintain folder structure order
    video_files.sort(key=lambda x: x[0])
    return video_files

def get_video_duration(video_path):
    """
    Returns the duration of a video in seconds.
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"⚠️ Warning: Could not read duration for {video_path}. Error: {e}")
        return None

MAX_VIDEO_DURATION = 21600  # 6 hours in seconds

def convert_videos(folder_path, video_files):
    """
    Converts videos to a uniform format (same codec, resolution, frame rate, etc.).
    Skips videos with no valid duration.
    """
    converted_folder = os.path.join(folder_path, "converted_videos")
    os.makedirs(converted_folder, exist_ok=True)
    converted_files = []

    # ✅ Filter out videos with no valid duration
    video_files = [f for f in video_files if get_video_duration(f) is not None]

    if not video_files:
        print(f"⚠️ No valid videos to convert in {folder_path}. Skipping...")
        return []

    print(f"🔄 Starting video conversion... (Timeout: {CONVERT_TIMEOUT // 3600} hours)")

    start_time = time.time()
    for video in video_files:
        # Use only the filename for the converted file, not the full subfolder path
        converted_video = os.path.join(converted_folder, os.path.basename(video))

        try:
            subprocess.run(
                ["ffmpeg", "-i", video, 
                 "-vf", "scale=1280:720",  # ✅ Ensures all videos are 720p
                 "-r", "30",               # ✅ Sets frame rate to 30 FPS
                 "-c:v", "libx264", 
                 "-preset", "fast", 
                 "-crf", "23", 
                 "-c:a", "aac", 
                 "-b:a", "128k", 
                 "-strict", "experimental", 
                 converted_video],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=CONVERT_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            print(f"⏳ Conversion **timed out** after {CONVERT_TIMEOUT // 3600} hours! Aborting this subfolder...")
            return []  # Return an empty list to indicate failure

        converted_files.append(converted_video)

        elapsed_time = time.time() - start_time
        if elapsed_time > CONVERT_TIMEOUT:
            print("⏳ Total conversion exceeded allowed time. Aborting conversion...")
            return []

    print("✅ Video conversion complete!")
    return converted_files

def try_merge_videos(folder_path, video_files, expected_duration, merge_attempt):
    """
    Merges videos using CPU processing only (no GPU acceleration for VMs).
    Skips videos with no valid duration.
    """
    file_list_path = os.path.join(folder_path, "file_list.txt")
    merged_video_path = os.path.join(folder_path, "merged_video.mp4")

    # ✅ Filter out videos with no valid duration
    video_files = [f for f in video_files if get_video_duration(f) is not None]

    if not video_files:
        print(f"⚠️ No valid videos to merge in {folder_path}. Skipping...")
        return None

    # Create the file list with full paths
    with open(file_list_path, "w", encoding="utf-8") as f:
        for video_file in video_files:
            f.write(f"file '{video_file}'\n")

    print(f"🔗 Attempt {merge_attempt}: Merging {len(video_files)} videos... (Timeout: {MERGE_TIMEOUT // 60} min)")
    print("Videos to merge:")
    for video in video_files:
        print(f"  - {os.path.basename(video)}")

    try:
        subprocess.run(
            ["ffmpeg",
                "-f", "concat", "-safe", "0", "-i", file_list_path,
                "-c:v", "libx264",  # ✅ CPU-based encoding only
                "-preset", "fast",  # ✅ Balanced speed/quality
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-strict", "experimental",
                merged_video_path
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=MERGE_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        print(f"⏳ Merge attempt {merge_attempt} **timed out** after {MERGE_TIMEOUT // 60} minutes! Skipping...")
        return None

    merged_duration = get_video_duration(merged_video_path)
    if merged_duration and abs(merged_duration - expected_duration) <= 5:
        print(f"✅ Merge successful! Duration: {merged_duration:.2f} sec")
        return merged_video_path
    else:
        print(f"❌ Merge failed. Merged duration: {merged_duration:.2f} sec, Expected: {expected_duration:.2f} sec")
        if os.path.exists(merged_video_path):
            os.remove(merged_video_path)
        return None

def create_timestamps(video_files, durations):
    """
    Create a description with timestamps for each video.
    """
    description = "Timeline:\n\n"
    current_time = 0
    
    for (rel_path, _), duration in zip(video_files, durations):
        if duration:
            # Format timestamp as HH:MM:SS
            hours = int(current_time // 3600)
            minutes = int((current_time % 3600) // 60)
            seconds = int(current_time % 60)
            timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Add timestamp and video name to description
            description += f"{timestamp} - {rel_path}\n"
            current_time += duration
    
    return description

def process_tutorial_folder(tutorial_path):
    """Process a single tutorial folder, merging ALL videos from ALL subfolders into one video."""
    try:
        print(f"\n📂 Processing tutorial: {tutorial_path}")
        
        # Check if already processed
        youtube_link_path = os.path.join(tutorial_path, "youtube lin.txt")
        if os.path.exists(youtube_link_path):
            print(f"⏭️ Skipping {tutorial_path} - Already uploaded (youtube_link.txt exists)")
            return
            
        # Get all video files with their relative paths for timestamps
        video_files = get_all_video_files(tutorial_path)
        if not video_files:
            print(f"⚠️ No video files found in {tutorial_path}")
            return
            
        # Split into paths and full paths
        rel_paths, full_paths = zip(*video_files)
        
        # Convert videos if needed
        try:
            converted_folder = os.path.join(tutorial_path, "converted_videos")
            converted_files = convert_videos(tutorial_path, full_paths)
            if not converted_files:
                print(f"❌ Failed to convert videos in {tutorial_path}, continuing to next folder")
                return
        except Exception as e:
            print(f"❌ Error converting videos in {tutorial_path}: {str(e)}")
            print("Continuing to next folder...")
            return
            
        # Get durations for timestamps
        durations = [get_video_duration(v) for v in converted_files]
        if None in durations:
            print(f"❌ Failed to get duration for some videos in {tutorial_path}")
            return
            
        # Create description with timestamps
        description = create_timestamps(video_files, durations)
        
        # Try to merge videos
        try:
            expected_duration = sum(d for d in durations if d is not None)
            merged_video = try_merge_videos(tutorial_path, converted_files, expected_duration, merge_attempt=1)
            if not merged_video:
                print(f"❌ Failed to merge videos in {tutorial_path}, continuing to next folder")
                return
        except Exception as e:
            print(f"❌ Error merging videos in {tutorial_path}: {str(e)}")
            print("Continuing to next folder...")
            return
            
        # Try to upload to YouTube
        try:
            video_url = upload_to_youtube(merged_video, tutorial_path, description)
            print(f"✅ Successfully processed {tutorial_path}")
            print(f"🔗 Video URL: {video_url}")
            
            # Only clean up if upload was successful
            cleanup_after_upload(tutorial_path, merged_video, converted_folder)
            
        except Exception as e:
            print(f"❌ Error uploading video from {tutorial_path}: {str(e)}")
            print("Continuing to next folder...")
            return
            
    except Exception as e:
        print(f"❌ Unexpected error processing {tutorial_path}: {str(e)}")
        print("Continuing to next folder...")
        return

def process_software_category(category_path):
    """
    Process all tutorials within a software category (e.g., Revit MEP or Power BI).
    Handles the three-level structure: Software -> Provider -> Tutorial.
    """
    try:
        print(f"\n🔍 Processing software category: {category_path}")
        
        # Get all provider folders (Lynda, Udemy, etc.)
        for provider in sorted(os.listdir(category_path)):
            try:
                provider_path = os.path.join(category_path, provider)
                if not os.path.isdir(provider_path):
                    continue
                    
                print(f"\n👥 Processing provider: {provider}")
                
                # Get all tutorial folders for this provider
                for tutorial in sorted(os.listdir(provider_path)):
                    try:
                        tutorial_path = os.path.join(provider_path, tutorial)
                        if not os.path.isdir(tutorial_path):
                            continue
                            
                        # Check if this is a tutorial folder or if it contains tutorial folders
                        if is_tutorial_folder(tutorial_path):
                            process_tutorial_folder(tutorial_path)
                        else:
                            # Check subfolders for tutorials
                            for subfolder in sorted(os.listdir(tutorial_path)):
                                try:
                                    subfolder_path = os.path.join(tutorial_path, subfolder)
                                    if os.path.isdir(subfolder_path) and is_tutorial_folder(subfolder_path):
                                        process_tutorial_folder(subfolder_path)
                                except Exception as e:
                                    print(f"❌ Error processing subfolder {subfolder}: {str(e)}")
                                    print("Continuing to next folder...")
                                    continue
                                    
                    except Exception as e:
                        print(f"❌ Error processing tutorial {tutorial}: {str(e)}")
                        print("Continuing to next folder...")
                        continue
                        
            except Exception as e:
                print(f"❌ Error processing provider {provider}: {str(e)}")
                print("Continuing to next provider...")
                continue
                
    except Exception as e:
        print(f"❌ Error processing software category {category_path}: {str(e)}")
        print("Script will exit...")
        return

def upload_to_youtube(video_path, tutorial_path, description="Tutorial video compilation"):
    """
    Uploads a video to YouTube with a title based on the folder structure.
    Handles quota limits with retry mechanism.
    """
    # Check if already uploaded - now checking in the same directory as the merged video
    youtube_link_path = os.path.join(os.path.dirname(video_path), "youtube lin.txt")
    if os.path.exists(youtube_link_path):
        print(f"⏭️ Video already uploaded for {tutorial_path}")
        with open(youtube_link_path, 'r') as f:
            return f.readlines()[-1].strip()  # Return the URL from the last line
    
    # Check quota state
    quota_reset_time = get_quota_state()
    if quota_reset_time:
        current_time = datetime.utcnow()
        if current_time < quota_reset_time:
            wait_time = (quota_reset_time - current_time).total_seconds()
            print(f"⏳ YouTube quota exceeded. Waiting until {quota_reset_time.isoformat()} (about {wait_time/3600:.1f} hours)")
            time.sleep(wait_time)
    
    # Split the path to extract meaningful parts
    path_parts = tutorial_path.split(os.path.sep)
    
    try:
        # Find key folder indices
        tutorials_idx = path_parts.index("05 Tutorials")
        software_parts = path_parts[tutorials_idx+1:tutorials_idx+3]
        provider = path_parts[tutorials_idx+3]
        course_name = path_parts[tutorials_idx+4:]
        
        # Construct title
        title_parts = software_parts + [provider] + course_name
        title = " - ".join(title_parts)
        
    except (ValueError, IndexError):
        title = " - ".join(path_parts[-4:])
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"📤 Uploading: {title}... (Attempt {attempt + 1}/{MAX_RETRIES})")
            youtube = get_authenticated_service()
            request = youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                        "categoryId": "27"
                    },
                    "status": {
                        "privacyStatus": "unlisted"
                    }
                },
                media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
            )
            
            _, response = request.next_chunk()
            video_url = f"https://www.youtube.com/watch?v={response['id']}"
            
            # Save the link in "youtube lin.txt" next to the merged video
            with open(youtube_link_path, "w") as f:
                f.write(f"{title}\n{video_url}\n")
            
            print(f"✅ Upload complete! Video URL: {video_url}")
            print(f"📝 Link saved in: {youtube_link_path}")
            return video_url
            
        except ResumableUploadError as e:
            if "uploadLimitExceeded" in str(e):
                reset_time, wait_time = handle_quota_error()
                print(f"⚠️ Upload limit exceeded. Quota will reset at {reset_time.isoformat()}")
                print(f"⏳ Waiting {wait_time/3600:.1f} hours before retrying...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ Upload failed with error: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    print(f"⏳ Retrying in {RETRY_DELAY/3600:.1f} hours...")
                    time.sleep(RETRY_DELAY)
                    continue
                raise
        except Exception as e:
            print(f"❌ Upload failed with error: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print(f"⏳ Retrying in {RETRY_DELAY/3600:.1f} hours...")
                time.sleep(RETRY_DELAY)
                continue
            raise
    
    raise Exception(f"Failed to upload video after {MAX_RETRIES} attempts")

if __name__ == "__main__":
    try:
        # First check YouTube authentication
        print("\n🔑 Checking YouTube authentication...")
        youtube = get_authenticated_service()
        print("✅ YouTube authentication successful!")
        
        # Create GUI root window (will be hidden)
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Show input dialog
        software_path = simpledialog.askstring(
            "Input Path", 
            "Enter the tutorial folder path:"
        )
        
        if software_path:  # If user didn't cancel
            software_path = software_path.strip()
            print(f"\n📂 Selected path: {software_path}")
            
            if not os.path.exists(software_path):
                print(f"❌ Error: Path does not exist: {software_path}")
                messagebox.showerror("Error", "The specified path does not exist.")
            else:
                print("\n🎬 Starting video processing...")
                print(f"📁 Directory contents:")
                for item in os.listdir(software_path):
                    item_path = os.path.join(software_path, item)
                    if os.path.isdir(item_path):
                        print(f"  📂 {item}")
                    else:
                        print(f"  📄 {item}")
                
                # Process the folder directly
                process_tutorial_folder(software_path)
                print("\n✅ Processing complete!")
                messagebox.showinfo("Complete", "Processing complete!")
        else:
            print("❌ No path selected. Exiting...")
        
        root.destroy()  # Clean up the hidden window
        
    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
        print("Please ensure you have proper YouTube credentials and try again.")
        if 'root' in locals():
            root.destroy()
