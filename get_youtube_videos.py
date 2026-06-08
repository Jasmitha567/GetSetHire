from googleapiclient.discovery import build

YOUTUBE_API_KEY = "YOUR_API_KEY"

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_videos_for_skill(skill):
    request = youtube.search().list(
        part='snippet',
        q=f'{skill} tutorial for beginners',
        type='video',
        maxResults=3
    )
    response = request.execute()

    videos = []

    for item in response['items']:
        video_id = item['id']['videoId']
        title = item['snippet']['title']

        videos.append({
            "video_id": video_id,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "embed_url": f"https://www.youtube.com/embed/{video_id}"
        })

    return videos