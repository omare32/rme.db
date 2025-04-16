#!/usr/bin/env python3
import os
import glob
import json
import time
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime

import ffmpeg
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_processing.log'),
        logging.StreamHandler()
    ]
)

class VideoProcessor:
    def __init__(self, base_path: str, client_secrets_file: str):
        self.base_path = Path(base_path)
        self.client_secrets_file = client_secrets_file
        self.converted_videos_dir = self.base_path / "converted_videos"
        self.processed_courses_file = self.base_path / "processed_courses.json"
        self.youtube = None
        self.processed_courses = self._load_processed_courses()
        
        # Create converted_videos directory if it doesn't exist
        self.converted_videos_dir.mkdir(exist_ok=True)

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
        """Authenticate with YouTube API."""
        if not self.youtube:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file,
                ['https://www.googleapis.com/auth/youtube.upload']
            )
            credentials = flow.run_local_server(port=0)
            self.youtube = build('youtube', 'v3', credentials=credentials)

    def convert_video(self, input_path: str, output_path: str):
        """Convert video to 720p 30fps format."""
        try:
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(stream, output_path,
                                 vf='scale=-1:720',
                                 r=30,
                                 video_bitrate='2000k',
                                 audio_bitrate='192k')
            ffmpeg.run(stream, overwrite_output=True)
            return True
        except ffmpeg.Error as e:
            logging.error(f"Error converting video {input_path}: {str(e)}")
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

    def generate_timestamps(self, video_files: List[str]) -> str:
        """Generate timestamps for video description."""
        timestamps = []
        current_time = 0
        
        for video_file in video_files:
            video_name = Path(video_file).stem
            duration = self.get_video_duration(video_file)
            
            hours = int(current_time // 3600)
            minutes = int((current_time % 3600) // 60)
            seconds = int(current_time % 60)
            
            timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d} - {video_name}"
            timestamps.append(timestamp)
            
            current_time += duration
        
        return "\n".join(timestamps)

    def merge_videos(self, video_files: List[str], output_path: str) -> bool:
        """Merge multiple videos into a single file."""
        try:
            with open('file_list.txt', 'w') as f:
                for video_file in video_files:
                    f.write(f"file '{video_file}'\n")
            
            ffmpeg.input('file_list.txt', f='concat', safe=0)\
                  .output(output_path, c='copy')\
                  .run(overwrite_output=True)
            
            os.remove('file_list.txt')
            return True
        except Exception as e:
            logging.error(f"Error merging videos: {str(e)}")
            return False

    def upload_to_youtube(self, video_path: str, title: str, description: str) -> bool:
        """Upload video to YouTube."""
        try:
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
                    logging.info(f"Uploaded {int(status.progress() * 100)}%")

            logging.info(f"Upload Complete! Video ID: {response['id']}")
            return True

        except HttpError as e:
            if e.resp.status in [403, 429]:  # Quota exceeded
                logging.warning("YouTube quota exceeded. Waiting 24 hours...")
                time.sleep(86400)  # Wait 24 hours
                return self.upload_to_youtube(video_path, title, description)
            else:
                logging.error(f"YouTube upload error: {str(e)}")
                return False

    def process_course(self, course_path: str):
        """Process a single course folder."""
        course_name = Path(course_path).name
        
        if course_name in self.processed_courses:
            logging.info(f"Course {course_name} already processed. Skipping...")
            return
        
        logging.info(f"Processing course: {course_name}")
        
        # Get all video files in the course folder
        video_files = []
        for ext in ('*.mp4', '*.avi', '*.mkv'):
            video_files.extend(glob.glob(str(Path(course_path) / '**' / ext), recursive=True))
        
        video_files.sort()  # Ensure correct order
        
        if not video_files:
            logging.warning(f"No video files found in {course_path}")
            return
        
        # Convert all videos to consistent format
        converted_files = []
        for video_file in video_files:
            output_file = self.converted_videos_dir / f"{Path(video_file).stem}_converted.mp4"
            if self.convert_video(video_file, str(output_file)):
                converted_files.append(str(output_file))
        
        if not converted_files:
            logging.error(f"No videos were successfully converted for {course_name}")
            return
        
        # Merge converted videos
        merged_video_path = self.converted_videos_dir / f"{course_name}_merged.mp4"
        if not self.merge_videos(converted_files, str(merged_video_path)):
            logging.error(f"Failed to merge videos for {course_name}")
            return
        
        # Generate timestamps
        timestamps = self.generate_timestamps(video_files)
        description = f"Tutorial Contents:\n\n{timestamps}\n\nAutomatically processed and uploaded."
        
        # Upload to YouTube
        if self.upload_to_youtube(str(merged_video_path), course_name, description):
            # Mark as processed and clean up
            self.processed_courses[course_name] = {
                'processed_date': datetime.now().isoformat(),
                'video_count': len(video_files)
            }
            self._save_processed_courses()
            
            # Clean up converted files
            for file in converted_files:
                os.remove(file)
            os.remove(merged_video_path)
            
            logging.info(f"Successfully processed and uploaded {course_name}")
        else:
            logging.error(f"Failed to upload {course_name} to YouTube")

    def process_all_courses(self):
        """Process all course folders in the base directory."""
        course_folders = [f for f in self.base_path.iterdir() if f.is_dir() and f != self.converted_videos_dir]
        
        for course_folder in course_folders:
            self.process_course(str(course_folder))

def main():
    base_path = "09.other.projects/01.youtube/04.merge.and.upload"
    client_secrets_file = "client_secrets.json"  # You'll need to provide this
    
    processor = VideoProcessor(base_path, client_secrets_file)
    processor.process_all_courses()

if __name__ == "__main__":
    main()
