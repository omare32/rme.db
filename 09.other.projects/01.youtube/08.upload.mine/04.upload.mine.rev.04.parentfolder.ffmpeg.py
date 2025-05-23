import os
import pickle
import tkinter as tk
from tkinter import filedialog
import subprocess
import shlex
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS_FILE = 'client_secret.emc.json'
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv']
MERGED_OUTPUT_DIR = 'D:/merged'

os.makedirs(MERGED_OUTPUT_DIR, exist_ok=True)

def get_parent_directory():
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory(title="Select Parent Directory to Scan for Video Folders")
    root.destroy()
    return directory

def find_video_folders(parent_dir):
    video_folders = []
    for root, dirs, files in os.walk(parent_dir):
        if any(file.lower().endswith(tuple(VIDEO_EXTENSIONS)) for file in files):
            video_folders.append(root)
    return video_folders

def find_videos(directory):
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                video_files.append(os.path.join(root, file))
    return sorted(video_files)

def merge_videos_ffmpeg(video_files, output_path):
    filelist_path = 'ffmpeg_filelist.txt'
    with open(filelist_path, 'w', encoding='utf-8') as f:
        for vf in video_files:
            f.write(f"file '{vf.replace('\\', '/').replace("'", "'\\''")}'\n")
    cmd = f"ffmpeg -f concat -safe 0 -i {filelist_path} -c copy \"{output_path}\""
    print(f"Running: {cmd}")
    result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if result.returncode != 0:
        print('ffmpeg error:', result.stderr)
        raise RuntimeError('ffmpeg merge failed')
    os.remove(filelist_path)

def authenticate_youtube():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('youtube', 'v3', credentials=creds)

def get_last_4_folders(path):
    parts = os.path.normpath(path).split(os.sep)
    return ' - '.join(parts[-4:]) if len(parts) >= 4 else os.path.basename(path)

def upload_video(youtube, file_path, title):
    body = {
        'snippet': {
            'title': title,
            'description': 'Merged video uploaded by automated script',
            'tags': [],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'private'
        }
    }
    media = MediaFileUpload(file_path, resumable=True)
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading {file_path}: {int(status.progress() * 100)}% done.")
    print(f"Upload Complete: {file_path}")
    # Compose YouTube link if upload succeeded
    video_id = response.get('id') if response else None
    youtube_url = f'https://youtu.be/{video_id}' if video_id else None
    return response, youtube_url

def main():
    parent_dir = get_parent_directory()
    if not parent_dir:
        print("No parent directory selected. Exiting.")
        return
    video_folders = find_video_folders(parent_dir)
    if not video_folders:
        print("No folders with videos found.")
        return
    youtube = authenticate_youtube()
    total_folders = len(video_folders)
    for idx, folder in enumerate(video_folders, 1):
        videos = find_videos(folder)
        if not videos:
            continue
        merged_title = get_last_4_folders(folder)
        merged_path = os.path.join(MERGED_OUTPUT_DIR, merged_title + '.mp4')
        print(f"[{idx}/{total_folders}] Merging {len(videos)} videos in: {folder}")
        try:
            merge_videos_ffmpeg(videos, merged_path)
            print(f"[{idx}/{total_folders}] Merged video saved to: {merged_path}")
            print(f"[{idx}/{total_folders}] Uploading video to YouTube: {merged_title}")
            response, youtube_url = upload_video(youtube, merged_path, merged_title)
            print(f"[{idx}/{total_folders}] Upload complete: {merged_title}")
        except Exception as e:
            print(f"[{idx}/{total_folders}] Failed to process {folder}: {e}")
            youtube_url = None
        # Only cleanup and create .txt file if upload succeeded and link is available
        if youtube_url and os.path.exists(merged_path):
            os.remove(merged_path)
            print(f"[{idx}/{total_folders}] Deleted merged video: {merged_path}")
            txt_path = os.path.splitext(merged_path)[0] + ".txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"YouTube Link: {youtube_url}\n")
            print(f"[{idx}/{total_folders}] Wrote YouTube link to: {txt_path}")

if __name__ == '__main__':
    main()
