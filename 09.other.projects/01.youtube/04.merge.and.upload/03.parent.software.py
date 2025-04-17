#!/usr/bin/env python3
import os
import glob
import json
import time
import shutil
import ssl
import urllib3
from pathlib import Path, WindowsPath
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import traceback
from google.auth.transport.requests import Request
import sys
import subprocess

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import ffmpeg
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configure logging
class FFmpegFilter(logging.Filter):
    def filter(self, record):
        # Filter out ffmpeg-related messages that aren't errors
        return not (('ffmpeg' in record.getMessage().lower() or 
                    'mpeg' in record.getMessage().lower()) and 
                   record.levelno < logging.ERROR)

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO
    format='%(asctime)s - %(message)s',  # Simplified format
    datefmt='%H:%M:%S',  # Only show time for better readability
    handlers=[
        logging.FileHandler('video_processing.log'),
        logging.StreamHandler(sys.stdout)  # Explicitly use stdout
    ]
)

# Force immediate flush of stdout
sys.stdout.reconfigure(line_buffering=True)  # For Python 3.7+

# Add filter to both handlers
ffmpeg_filter = FFmpegFilter()
for handler in logging.getLogger().handlers:
    handler.addFilter(ffmpeg_filter)

# Suppress other verbose loggers
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.getLogger('googleapiclient.discovery').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

# Add a test log message
logging.info("Video processing script started")

TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service(client_secrets_file: str):
    """Get authenticated YouTube service, reusing token if available."""
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logging.info("📄 Loaded existing token")
        except Exception as e:
            logging.error(f"❌ Error loading token: {str(e)}")
            creds = None

    # If token doesn't exist or is invalid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logging.info("🔄 Token expired, refreshing...")
                creds.refresh(Request())
                logging.info("✅ Token refreshed successfully")
            except Exception as e:
                logging.error(f"❌ Error refreshing token: {str(e)}")
                creds = None

        # If still no valid credentials, need to authenticate
        if not creds:
            try:
                logging.info("🌐 Opening browser for authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
                logging.info("✅ Authentication successful")
            except Exception as e:
                logging.error(f"❌ Authentication failed: {str(e)}")
                raise

        # Save the credentials for future use
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            logging.info("💾 Token saved successfully")
        except Exception as e:
            logging.error(f"❌ Error saving token: {str(e)}")

    try:
        service = build('youtube', 'v3', credentials=creds, cache_discovery=False)
        logging.info("✅ YouTube service created successfully")
        return service
    except Exception as e:
        logging.error(f"❌ Error creating YouTube service: {str(e)}")
        raise

def get_all_video_files(folder_path: str) -> List[Tuple[str, str]]:
    """Get all video files in folder and subfolders with their relative paths."""
    video_files = []
    base_path = Path(folder_path)
    
    for ext in ('*.mp4', '*.avi', '*.mkv'):
        for file_path in Path(folder_path).rglob(ext):
            # Get relative path for timestamps
            rel_path = str(file_path.relative_to(base_path))
            video_files.append((str(file_path), rel_path))
    
    # Sort by full path to maintain consistent order
    return sorted(video_files)

def collect_and_prepare_videos(folder_path: str) -> List[Tuple[str, str]]:
    """
    Collect all videos from subfolders, rename them with simple numeric prefixes, and move to course folder.
    Returns list of (full_path, relative_path) tuples.
    """
    try:
        # Get all subfolders sorted by their numeric prefix
        subfolders = []
        for item in os.listdir(folder_path):
            if os.path.isdir(os.path.join(folder_path, item)):
                # Extract numeric prefix if exists
                prefix = ''.join(filter(str.isdigit, item.split('.')[0]))
                subfolders.append((prefix, item))
        
        # Sort subfolders by numeric prefix
        subfolders.sort(key=lambda x: (int(x[0]) if x[0] else float('inf'), x[1]))
        
        # Collect and rename videos
        video_files = []
        video_counter = 1
        
        for _, subfolder in subfolders:
            subfolder_path = os.path.join(folder_path, subfolder)
            
            # Get videos in current subfolder
            for ext in ('*.mp4', '*.avi', '*.mkv'):
                for file_path in glob.glob(os.path.join(subfolder_path, "**", ext), recursive=True):
                    # Create new name with just sequence number
                    new_name = f"{video_counter:03d}.mp4"
                    new_path = os.path.join(folder_path, new_name)
                    
                    # Copy video to course folder with new name
                    try:
                        shutil.copy2(file_path, new_path)
                        # Store both the full path and the simple relative path
                        rel_path = os.path.join(subfolder, os.path.basename(file_path))
                        video_files.append((new_path, rel_path))
                        video_counter += 1
                        logging.info(f"Copied and renamed: {os.path.basename(file_path)} -> {new_name}")
                    except Exception as e:
                        logging.error(f"Error copying {file_path}: {str(e)}")
        
        return video_files
        
    except Exception as e:
        logging.error(f"Error collecting videos: {str(e)}")
        return []

def is_course_folder(folder_path: str) -> bool:
    """Check if folder is a course folder (contains numbered subfolders)."""
    try:
        items = os.listdir(folder_path)
        # Check if any subfolder starts with a number followed by dot
        return any(os.path.isdir(os.path.join(folder_path, item)) and 
                  any(c.isdigit() for c in item.split('.')[0])
                  for item in items)
    except Exception as e:
        logging.error(f"Error checking course folder: {str(e)}")
        return False

def get_structured_title(input_path: str) -> str:
    """Generate a structured title from the folder path."""
    try:
        # Convert path to Path object and get parts
        path = Path(input_path)
        parts = list(path.parts)
        
        # Find the indices of key folders
        try:
            google_idx = [i for i, part in enumerate(parts) if part.lower() == 'google'][0]
            sheets_idx = [i for i, part in enumerate(parts) if part.lower() == 'sheets'][0]
            lynda_idx = [i for i, part in enumerate(parts) if part.lower() == 'lynda'][0]
            
            # Get the course name (parent folder of numbered subfolders)
            if is_course_folder(input_path):
                course_name = path.name
    else:
                course_name = path.parent.name
            
            # Format: "Google - Sheets - Lynda - {Course Name}"
            return f"Google - Sheets - Lynda - {course_name}"
        except (IndexError, ValueError) as e:
            logging.error(f"Error parsing path structure: {str(e)}")
            return path.name
            
    except Exception as e:
        logging.error(f"Error in get_structured_title: {str(e)}")
        return os.path.basename(input_path)

def find_course_folder(folder_path: str) -> str:
    """Find the actual course folder that contains the videos."""
    try:
        path = Path(folder_path)
        
        # Check if current folder has videos
        video_files = []
        for ext in ('*.mp4', '*.avi', '*.mkv'):
            video_files.extend(glob.glob(os.path.join(folder_path, "**", ext), recursive=True))
            
        if not video_files:
            return folder_path
            
        # Get the parent folder of the first video
        first_video = Path(video_files[0])
        return str(first_video.parent)
        
    except Exception as e:
        logging.error(f"Error finding course folder: {str(e)}")
        return folder_path

def cleanup_and_save_link(folder_path: str, video_id: str, title: str):
    """Clean up original files and save YouTube link."""
    try:
        # Find the actual course folder
        course_folder = find_course_folder(folder_path)
        logging.info(f"Found course folder: {course_folder}")
        
        # Create youtube link.txt in the course folder
        link_file = os.path.join(course_folder, "youtube link.txt")
        with open(link_file, 'w') as f:
            f.write(f"Title: {title}\n")
            f.write(f"URL: https://www.youtube.com/watch?v={video_id}\n")
            f.write(f"Uploaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        logging.info(f"Created link file: {link_file}")
        
        # Delete converted_videos folder if it exists
        converted_videos_dir = os.path.join(course_folder, "converted_videos")
        if os.path.exists(converted_videos_dir):
            try:
                shutil.rmtree(converted_videos_dir)
                logging.info(f"Cleaned up converted_videos folder: {converted_videos_dir}")
            except Exception as e:
                logging.error(f"Failed to delete converted_videos folder: {str(e)}")
        
        # Delete merged video if it exists
        merged_video = os.path.join(course_folder, f"{os.path.basename(course_folder)}_merged.mp4")
        if os.path.exists(merged_video):
            try:
                os.remove(merged_video)
                logging.info(f"Deleted merged video: {merged_video}")
            except Exception as e:
                logging.error(f"Failed to delete merged video: {str(e)}")
        
        # Delete original video folders
        for root, dirs, files in os.walk(course_folder, topdown=False):
            for dir in dirs:
                if any(dir.startswith(str(i)) for i in range(10)):  # Folders starting with numbers
                    dir_path = os.path.join(root, dir)
                    try:
                        shutil.rmtree(dir_path)
                        logging.info(f"Deleted folder: {dir}")
                    except Exception as e:
                        logging.error(f"Failed to delete folder {dir}: {str(e)}")
        
        logging.info(f"Cleanup completed for {course_folder}")
    except Exception as e:
        logging.error(f"Error during cleanup: {str(e)}")

class VideoProcessor:
    def __init__(self, base_path: str, client_secrets_file: str):
        self.base_path = Path(base_path)
        self.client_secrets_file = client_secrets_file
        self.processed_courses_file = self.base_path / "processed_courses.json"
        self.youtube = None
        self.processed_courses = self._load_processed_courses()

    def _load_processed_courses(self) -> Dict[str, dict]:
        """Load the list of already processed courses."""
        if self.processed_courses_file.exists():
            with open(self.processed_courses_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_processed_courses(self):
        """Save the list of processed courses."""
        with open(self.processed_courses_file, 'w') as f:
            json.dump(self.processed_courses, f, indent=4)

    def _authenticate_youtube(self):
        """Authenticate with YouTube API using token persistence."""
        if not self.youtube:
            try:
                self.youtube = get_authenticated_service(self.client_secrets_file)
                logging.info("✅ Successfully authenticated with YouTube")
            except Exception as e:
                logging.error(f"❌ Failed to authenticate with YouTube: {str(e)}")
                raise

    def convert_video(self, input_path: str, output_path: str) -> bool:
        """Convert video to 720p 30fps format with improved error handling and quality control."""
        try:
            # Get input video size
            input_size = os.path.getsize(input_path)
            input_mb = input_size / (1024 * 1024)
            logging.info(f"Input video size: {input_mb:.2f} MB")
            
            # Get input video information
            probe = ffmpeg.probe(input_path)
            video_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if not video_info:
                logging.error("No video stream found in input file")
                return False
            
            input_width = int(video_info.get('width', 0))
            input_height = int(video_info.get('height', 0))
            logging.info(f"Input video resolution: {input_width}x{input_height}")
            
            # Calculate target bitrate based on resolution and framerate
            pixels = 1280 * 720  # Target resolution
            target_video_bitrate = max(2000000, min(6000000, int(pixels * 30 * 0.1)))  # 0.1 bits per pixel
            target_video_bitrate_str = f"{target_video_bitrate // 1000}k"
            
            # Prepare audio parameters
            audio_params = {}
            if audio_info:
                # Keep original audio bitrate if it's reasonable, otherwise use 192k
                original_audio_bitrate = int(audio_info.get('bit_rate', 192000))
                audio_params = {
                    'audio_bitrate': f"{min(384000, max(128000, original_audio_bitrate)) // 1000}k",
                    'acodec': 'aac',
                    'ar': '48000'  # Standard audio sample rate
                }
            
            # Build the ffmpeg command with improved parameters
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(
                stream, 
                output_path,
                vf='scale=-2:720:flags=lanczos',  # High-quality scaling
                r=30,
                video_bitrate=target_video_bitrate_str,
                vcodec='libx264',
                preset='medium',
                g=60,  # GOP size = 2 seconds at 30fps
                pix_fmt='yuv420p',  # Widely compatible pixel format
                movflags='+faststart',  # Enable streaming
                **audio_params
            )
            
            # Run the conversion with progress monitoring
            process = ffmpeg.run_async(stream, pipe_stdout=True, pipe_stderr=True)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logging.error(f"FFmpeg conversion failed with return code {process.returncode}")
                if stderr:
                    logging.error(f"FFmpeg error output: {stderr.decode()}")
                return False
            
            # Verify output
            if os.path.exists(output_path):
                output_size = os.path.getsize(output_path)
                output_mb = output_size / (1024 * 1024)
                logging.info(f"Conversion complete - Output size: {output_mb:.2f} MB")
                
                # Verify the output video
                try:
                    output_probe = ffmpeg.probe(output_path)
                    output_video = next((s for s in output_probe['streams'] if s['codec_type'] == 'video'), None)
                    
                    if not output_video:
                        logging.error("Output file has no video stream")
                        return False
                    
                    # Check if duration is within 1% of original
                    orig_duration = float(probe['format']['duration'])
                    out_duration = float(output_probe['format']['duration'])
                    if abs(orig_duration - out_duration) > orig_duration * 0.01:
                        logging.error(f"Output duration ({out_duration:.2f}s) differs significantly from input ({orig_duration:.2f}s)")
                        return False
                    
                    return True
                    
                except Exception as e:
                    logging.error(f"Error verifying output video: {str(e)}")
                    return False
            else:
                logging.error("Conversion completed but output file not found")
                return False
                
        except ffmpeg.Error as e:
            logging.error("FFmpeg error during conversion:")
            if e.stdout:
                logging.error(f"FFmpeg stdout: {e.stdout.decode()}")
            if e.stderr:
                logging.error(f"FFmpeg stderr: {e.stderr.decode()}")
            return False
        except Exception as e:
            logging.error(f"Error converting video {input_path}: {str(e)}")
            logging.error(traceback.format_exc())
            return False

    def get_video_duration(self, file_path: str) -> float:
        """Get video duration in seconds."""
        try:
            probe = ffmpeg.probe(file_path)
            duration = float(probe['streams'][0]['duration'])
            return duration
        except Exception as e:
            logging.error(f"Error getting video duration for {file_path}: {str(e)}")
            return 0

    def get_total_duration(self, video_files: List[Tuple[str, str]]) -> float:
        """Get total duration of all videos."""
        total_duration = 0
        for full_path, _ in video_files:
            try:
                duration = self.get_video_duration(full_path)
                total_duration += duration
            except Exception as e:
                logging.error(f"Error getting duration for {full_path}: {str(e)}")
        return total_duration

    def validate_merged_video(self, merged_path: str, original_duration: float) -> bool:
        """Validate merged video duration is within 5% of original total."""
        try:
            merged_duration = self.get_video_duration(merged_path)
            duration_diff_percent = abs(merged_duration - original_duration) / original_duration * 100
            
            logging.info(f"Original total duration: {original_duration:.2f} seconds")
            logging.info(f"Merged video duration: {merged_duration:.2f} seconds")
            logging.info(f"Duration difference: {duration_diff_percent:.2f}%")
            
            if duration_diff_percent <= 5:
                logging.info("✅ Merged video duration is within acceptable range")
                return True
            else:
                logging.error(f"❌ Merged video duration differs by {duration_diff_percent:.2f}% from original")
                return False
        except Exception as e:
            logging.error(f"Error validating merged video: {str(e)}")
            return False

    def generate_timestamps(self, video_files: List[Tuple[str, str]], base_folder: str) -> str:
        """
        Generate timestamps for video description based on video durations.
        
        Args:
            video_files (List[Tuple[str, str]]): List of tuples containing (full_path, relative_path)
            base_folder (str): Base folder path for reference
            
        Returns:
            str: Formatted timestamps string
        """
        timestamps = []
        current_duration = 0
        
        for full_path, rel_path in video_files:
            # Get video duration
            duration = self.get_video_duration(full_path)
            
            # Format current timestamp (HH:MM:SS)
            hours = int(current_duration // 3600)
            minutes = int((current_duration % 3600) // 60)
            seconds = int(current_duration % 60)
            formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Remove file extension and sanitize the relative path
            display_name = os.path.splitext(rel_path)[0]
            # Replace problematic characters with safe alternatives
            display_name = (display_name
                          .replace('\\', '/')  # Normalize path separators
                          .replace('&', 'and')  # Replace & with 'and'
                          .replace('<', '(')    # Replace angle brackets
                          .replace('>', ')')
                          .replace('"', "'")    # Replace double quotes with single
                          .replace('|', '-'))   # Replace pipe with hyphen
            
            timestamp_str = f"{formatted_time} - {display_name}"
            timestamps.append(timestamp_str)
            current_duration += duration
        
        return '\n'.join(timestamps)

    def merge_videos(self, video_files: List[Tuple[str, str]], output_path: str) -> bool:
        """Merge multiple videos into a single file using direct stream copy."""
        file_list_path = 'file_list.txt'
        process = None
        try:
            # Calculate total size of input files
            total_input_size = 0
            for full_path, _ in video_files:
                if not os.path.exists(full_path):
                    logging.error(f"Video file not found: {full_path}")
                    return False
                total_input_size += os.path.getsize(full_path)
            
            total_input_mb = total_input_size / (1024 * 1024)
            logging.info(f"Total size of input videos: {total_input_mb:.2f} MB")
            
            # Create file list for ffmpeg
            logging.info(f"Creating file list for merging {len(video_files)} videos...")
            
            # Convert network path to UNC format
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logging.info(f"Created output directory: {output_dir}")
            
            # Write file list with proper path escaping
            with open(file_list_path, 'w', encoding='utf-8') as f:
                for full_path, _ in video_files:
                    # Escape single quotes and backslashes in path
                    escaped_path = full_path.replace("'", "'\\''").replace("\\", "\\\\")
                    f.write(f"file '{escaped_path}'\n")
            
            logging.info(f"Merging videos to: {output_path}")
            try:
                # Build complex filter for concatenation
                inputs = []
                for i, (full_path, _) in enumerate(video_files):
                    inputs.extend(['-i', full_path])
                
                filter_complex = ''
                for i in range(len(video_files)):
                    filter_complex += f'[{i}:v:0][{i}:a:0]'
                filter_complex += f'concat=n={len(video_files)}:v=1:a=1[outv][outa]'
                
                # Use ffmpeg-python to construct the command
                stream = (
                    ffmpeg
                    .input('dummy')
                    .output(
                        output_path,
                        acodec='copy',
                        vcodec='copy',
                        **{'filter_complex': filter_complex}
                    )
                    .overwrite_output()
                )
                
                # Get the ffmpeg command
                cmd = ['ffmpeg'] + inputs + [
                    '-filter_complex', filter_complex,
                    '-map', '[outv]',
                    '-map', '[outa]',
                    '-c:v', 'copy',
                    '-c:a', 'copy',
                    output_path,
                    '-y'
                ]
                
                # Run ffmpeg command
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                out, err = process.communicate()
                
                if process.returncode != 0:
                    logging.error("FFmpeg process failed")
                    if err:
                        logging.error(f"FFmpeg error output: {err.decode()}")
                    return False
                
                if os.path.exists(output_path):
                    output_size = os.path.getsize(output_path)
                    output_mb = output_size / (1024 * 1024)
                    logging.info(f"Merge completed - Output size: {output_mb:.2f} MB")
                    
                    # Validate output size
                    if output_size < total_input_size * 0.5:  # Allow for more compression
                        logging.error(f"Output file size ({output_mb:.2f} MB) is significantly smaller than input size ({total_input_mb:.2f} MB)")
                        logging.error("The merge process may have failed or produced an incomplete file")
                        
                        # Check if output file is valid
                        try:
                            probe = ffmpeg.probe(output_path)
                            duration = float(probe['format']['duration'])
                            logging.info(f"Merged video duration: {duration:.2f} seconds")
                            
                            # Calculate total duration of input files
                            total_duration = 0
                            for full_path, _ in video_files:
                                input_probe = ffmpeg.probe(full_path)
                                total_duration += float(input_probe['format']['duration'])
                            
                            logging.info(f"Total input duration: {total_duration:.2f} seconds")
                            duration_diff = abs(duration - total_duration)
                            
                            if duration_diff > total_duration * 0.05:  # More than 5% difference
                                logging.error(f"Duration mismatch: merged={duration:.2f}s, total={total_duration:.2f}s")
                                return False
                        else:
                                logging.info("Duration validation passed, proceeding despite size difference")
                                return True
                                    
                    except Exception as e:
                            logging.error(f"Error validating merged video: {str(e)}")
                            return False
                            
                        return False
                        
                    return True
                else:
                    logging.error("Merge completed but output file not found")
                    return False
                    
            except ffmpeg.Error as e:
                logging.error(f"FFmpeg error during merge:")
                if e.stdout:
                    logging.error(f"FFmpeg stdout: {e.stdout.decode()}")
                if e.stderr:
                    logging.error(f"FFmpeg stderr: {e.stderr.decode()}")
                return False
                
    except Exception as e:
            logging.error(f"Error merging videos: {str(e)}")
            logging.error(traceback.format_exc())
            return False
        finally:
            # Clean up file list
            try:
                if os.path.exists(file_list_path):
                    os.remove(file_list_path)
            except Exception as e:
                logging.error(f"Failed to delete file list: {str(e)}")
            
            # Ensure ffmpeg process is terminated
            if process:
                try:
                    process.kill()
                except:
                    pass

    def upload_to_youtube(self, video_path: str, title: str, description: str) -> Optional[str]:
        """Upload video to YouTube."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if not self.youtube:
                    self._authenticate_youtube()
                
                body = {
                    'snippet': {
                        'title': title,
                        'description': description,
                        'tags': ['tutorial', 'education']
                    },
                    'status': {
                        'privacyStatus': 'private',
                        'selfDeclaredMadeForKids': False
                    }
                }

                insert_request = self.youtube.videos().insert(
                    part=','.join(body.keys()),
                    body=body,
                    media_body=MediaFileUpload(
                        video_path,
                        chunksize=-1,
                        resumable=True
                    )
                )

                response = None
                while response is None:
                    status, response = insert_request.next_chunk()
                    if status:
                        logging.info(f"📤 Uploaded {int(status.progress() * 100)}%")

                video_id = response['id']
                logging.info(f"✅ Upload Complete! Video ID: {video_id}")
                return video_id

            except HttpError as e:
                if e.resp.status in [403, 429]:  # Quota exceeded
                    wait_time = 86400  # 24 hours
                    logging.warning(f"⚠️ YouTube quota exceeded. Waiting {wait_time//3600} hours...")
                    time.sleep(wait_time)
                    retry_count += 1
                else:
                    logging.error(f"❌ YouTube upload error: {str(e)}")
                    retry_count += 1
                    time.sleep(3600)  # Wait 1 hour before retry
            except Exception as e:
                logging.error(f"❌ Unexpected error during upload: {str(e)}")
                retry_count += 1
                time.sleep(3600)  # Wait 1 hour before retry
        
        return None

    def process_tutorial_folder(self, folder_path: str):
        """Process all videos in a tutorial folder and its subfolders."""
        try:
            folder_path = str(folder_path)
            
            # Check if this is a course folder
            if is_course_folder(folder_path):
                logging.info(f"Found course folder: {folder_path}")
                self._process_single_course(folder_path)
            else:
                # Check subfolders for courses
                for item in os.listdir(folder_path):
                    subfolder_path = os.path.join(folder_path, item)
                    if os.path.isdir(subfolder_path) and is_course_folder(subfolder_path):
                        logging.info(f"Found course folder: {subfolder_path}")
                        self._process_single_course(subfolder_path)
                    
        except Exception as e:
            logging.error(f"Error scanning folder structure: {str(e)}")
            logging.error(traceback.format_exc())

    def _process_single_course(self, folder_path: str):
        """Process a single course folder."""
        try:
            folder_path = str(folder_path)
            course_name = get_structured_title(folder_path)
            
            if course_name in self.processed_courses:
                logging.info(f"Course '{course_name}' already processed - skipping")
                return

            logging.info(f"\n[1/4] 🎯 Starting process for: {course_name}")
            logging.info(f"Processing folder: {folder_path}")
            
            # Collect and prepare all videos
            video_files = collect_and_prepare_videos(folder_path)
            
            if not video_files:
                logging.warning(f"No video files found in {folder_path}")
                return
            
            logging.info(f"[2/4] 📁 Found {len(video_files)} videos to process")
            for idx, (_, rel_path) in enumerate(video_files, 1):
                logging.info(f"  Video {idx}: {rel_path}")
            
            # Calculate total duration
            total_duration = self.get_total_duration(video_files)
            if total_duration == 0:
                logging.error("Failed to calculate total duration of videos")
                return

            # Try merging the videos directly
            logging.info("[3/4] 🔄 Attempting direct merge without conversion...")
            merged_video_path = os.path.join(folder_path, f"{os.path.basename(folder_path)}_merged.mp4")
            
            merge_success = False
            try:
                if self.merge_videos(video_files, str(merged_video_path)):
                    if self.validate_merged_video(merged_video_path, total_duration):
                        logging.info("✅ Direct merge successful and validated")
                        merge_success = True
                    else:
                        logging.warning("⚠️ Direct merge failed validation - will try converting...")
                        try:
                            os.remove(merged_video_path)
                        except Exception as e:
                            logging.error(f"Failed to remove invalid merged video: {str(e)}")
                else:
                    logging.warning("⚠️ Direct merge failed - will try converting...")
            except Exception as e:
                logging.error(f"Error during direct merge: {str(e)}")
                logging.info("Proceeding with conversion...")
            
            if not merge_success:
                # Convert videos only if direct merge fails
                converted_videos_dir = os.path.join(folder_path, "converted_videos")
                os.makedirs(converted_videos_dir, exist_ok=True)
                
                converted_files = []
                total_files = len(video_files)
                
                for idx, (full_path, rel_path) in enumerate(video_files, 1):
                    output_file = os.path.join(converted_videos_dir, f"{os.path.splitext(rel_path)[0]}_converted.mp4")
                    logging.info(f"Converting [{idx}/{total_files}]: {rel_path}")
                    try:
                        if self.convert_video(full_path, str(output_file)):
                            converted_files.append((str(output_file), rel_path))
                            logging.info(f"✅ Successfully converted: {rel_path}")
                        else:
                            logging.error(f"Failed to convert: {rel_path}")
                    except Exception as e:
                        logging.error(f"Error converting {rel_path}: {str(e)}")
                
                if not converted_files:
                    logging.error(f"❌ No videos were successfully converted for {course_name}")
                    return

                # Try merging converted videos
                logging.info("Attempting to merge converted videos...")
                if not self.merge_videos(converted_files, str(merged_video_path)):
                    logging.error(f"❌ Failed to merge videos for {course_name}")
                    return
            
            if not os.path.exists(merged_video_path):
                logging.error(f"❌ Merged video file not found at: {merged_video_path}")
                return
            
            file_size_mb = os.path.getsize(merged_video_path) / (1024 * 1024)
            logging.info(f"Merged video size: {file_size_mb:.2f} MB")
            
            # Generate timestamps
            logging.info("[4/4] 📝 Generating video timestamps...")
            timestamps = self.generate_timestamps(video_files, folder_path)
            
            # Clean up the description
            description = "Tutorial Contents:\n\n"
            for line in timestamps.split('\n'):
                cleaned_line = ''.join(char if ord(char) < 128 else '-' for char in line)
                description += cleaned_line + '\n'
            description += "\nAutomatically processed and uploaded."
            
            # Upload to YouTube
            logging.info("📤 Uploading to YouTube...")
            video_id = self.upload_to_youtube(str(merged_video_path), course_name, description)
            
            if video_id:
                logging.info("🧹 Cleaning up files...")
                # Clean up and save link
                cleanup_and_save_link(folder_path, video_id, course_name)
                
                # Mark as processed
                self.processed_courses[course_name] = {
                    'processed_date': datetime.now().isoformat(),
                    'video_count': len(video_files),
                    'video_id': video_id
                }
                self._save_processed_courses()
                
                # Clean up all files
                try:
                    # Delete collected videos
                    for full_path, _ in video_files:
                        try:
                            os.remove(full_path)
                            logging.info(f"🗑️ Deleted collected video: {full_path}")
                        except Exception as e:
                            logging.error(f"Failed to delete collected video: {str(e)}")
                    
                    # Delete merged video
                    if os.path.exists(merged_video_path):
                        os.remove(merged_video_path)
                        logging.info(f"🗑️ Deleted merged video")
                    
                    # Delete converted_videos folder if it exists
                    if os.path.exists(converted_videos_dir):
                        shutil.rmtree(converted_videos_dir)
                        logging.info(f"🗑️ Cleaned up converted_videos folder")
                    
                    # Delete original video folders
                    for root, dirs, files in os.walk(folder_path, topdown=False):
                        for dir in dirs:
                            if any(dir.startswith(str(i)) for i in range(10)):
                                dir_path = os.path.join(root, dir)
                                try:
                                    shutil.rmtree(dir_path)
                                    logging.info(f"🗑️ Deleted folder: {dir}")
                                except Exception as e:
                                    logging.error(f"Failed to delete folder {dir}: {str(e)}")
                
                except Exception as e:
                    logging.error(f"Error during cleanup: {str(e)}")
                
                logging.info(f"✅ Successfully completed processing: {course_name}")
                logging.info(f"🔗 Video URL: https://www.youtube.com/watch?v={video_id}")
            else:
                logging.error(f"Failed to upload {course_name} to YouTube")

        except Exception as e:
            logging.error(f"Error processing course: {str(e)}")
            logging.error(traceback.format_exc())

    def process_all_courses(self):
        """Process all course folders in the base directory."""
        course_folders = [f for f in self.base_path.iterdir() if f.is_dir() and f != self.converted_videos_dir]
        
        for course_folder in course_folders:
            self.process_tutorial_folder(str(course_folder))

def main():
    import tkinter as tk
    from tkinter import simpledialog, messagebox
    
    # Configure logging to handle Unicode characters
    import sys
    sys.stdout.reconfigure(encoding='utf-8')  # For Python 3.7+
        
        # Create GUI root window (will be hidden)
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
    try:
        # First, try to authenticate with YouTube
        client_secrets_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret.json")
        logging.info(f"Using client secrets file: {client_secrets_file}")
        
        if not os.path.exists(client_secrets_file):
            error_msg = f"Client secrets file not found: {client_secrets_file}"
            logging.error(error_msg)
            messagebox.showerror("Error", error_msg)
            return

        # Create processor and authenticate
        try:
            processor = VideoProcessor("", client_secrets_file)  # Empty path for now
            processor._authenticate_youtube()  # Force authentication first
            logging.info("YouTube authentication successful")
        except Exception as e:
            error_msg = f"Failed to authenticate with YouTube: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            messagebox.showerror("Error", error_msg)
            return

        # Now show input dialog for folder selection
        default_path = r"H:\Projects Control (PC)\10 Backup\05 Tutorials\Google\Maps\Udemy\Google Maps Seo - The 4 Pillars To Rank Your Website Page 1"
        input_path = simpledialog.askstring(
            "Input Path", 
            "Enter the tutorial folder path:",
            initialvalue=default_path
        )
        
        if input_path:  # If user didn't cancel
            input_path = input_path.strip()
            input_path = input_path.replace('\\', '/')  # Convert backslashes to forward slashes
            logging.info(f"Selected path: {input_path}")

            try:
                # Try to normalize the network path
                if input_path.startswith('//'):
                    logging.info("Network path detected, attempting to access...")
                    
                # Test directory access
                try:
                    contents = os.listdir(input_path)
                    logging.info("Successfully accessed directory")
                    logging.info(f"Found {len(contents)} items in directory")
                except Exception as e:
                    error_msg = f"Cannot access directory: {str(e)}"
                    logging.error(error_msg)
                    logging.error(traceback.format_exc())
                    messagebox.showerror("Error", error_msg)
                    return

                if not os.path.exists(input_path):
                    error_msg = f"Path does not exist: {input_path}"
                    logging.error(error_msg)
                    messagebox.showerror("Error", error_msg)
                    return

                logging.info("Starting video processing...")
                logging.info(f"Directory contents:")
                
                try:
                    video_count = 0
                    total_size = 0
                    for item in os.listdir(input_path):
                        item_path = os.path.join(input_path, item)
                        try:
                            if os.path.isdir(item_path):
                                logging.info(f"  DIR: {item}")
            else:
                                size_mb = os.path.getsize(item_path) / (1024 * 1024)
                                if item.lower().endswith(('.mp4', '.avi', '.mkv')):
                                    video_count += 1
                                    total_size += size_mb
                                    logging.info(f"  VIDEO: {item} ({size_mb:.2f} MB)")
                    else:
                                    logging.info(f"  FILE: {item} ({size_mb:.2f} MB)")
                        except Exception as e:
                            logging.error(f"Error accessing {item}: {str(e)}")
                            
                    logging.info(f"\nFound {video_count} videos, total size: {total_size:.2f} MB")
                except Exception as e:
                    error_msg = f"Error listing directory contents: {str(e)}"
                    logging.error(error_msg)
                    logging.error(traceback.format_exc())
                    messagebox.showerror("Error", error_msg)
                    return

                # Process the folder
                processor.process_tutorial_folder(input_path)
                
                logging.info("Processing complete!")
                messagebox.showinfo("Complete", "Processing complete!")
            
            except Exception as e:
                error_msg = f"Error during video processing: {str(e)}"
                logging.error(error_msg)
                logging.error(traceback.format_exc())
                messagebox.showerror("Error", error_msg)

        else:
            logging.info("No path selected. Exiting...")
    except Exception as e:
        error_msg = f"Error processing directory: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        messagebox.showerror("Error", error_msg)
    finally:
            root.destroy()

if __name__ == "__main__":
    main()
