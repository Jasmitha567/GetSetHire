# search_youtube.py
from googleapiclient.discovery import build
import os

# You need a YouTube API key from Google Cloud Console
YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

skills = ['docker', 'kubernetes', 'terraform', 'linux', 'aws', 'git', 'jenkins']

for skill in skills:
    request = youtube.search().list(
        part='id',
        q=f'{skill} tutorial for beginners',
        type='video',
        maxResults=1
    )
    response = request.execute()
    if response['items']:
        video_id = response['items'][0]['id']['videoId']
        print(f'{skill}: "{video_id}"')