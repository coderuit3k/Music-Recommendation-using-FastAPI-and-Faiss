from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
# import matplotlib.pyplot as plt
# from PIL import Image
# import requests
# import webbrowser

load_dotenv()
ytb_api_key = os.getenv("YOUTUBE_API_KEY")


def get_youtube_description(name: str, artists: str):
    """
    Fetches the YouTube video description for a given song name and artists.

    Args:
        name (str): The name of the song.
        artists (str): The artists of the song.

    Returns:
        str: The YouTube video description if found, otherwise an empty string.
    """
    youtube = build(serviceName='youtube', version='v3', developerKey=ytb_api_key)
    query = f"{name} {artists} official music video"
    request = youtube.search().list(q=query, part='snippet', type='video', maxResults=1)
    response = request.execute()

    items = response.get('items', [])
    if not items:
        return None

    vid = items[0]['id']['videoId']

    video_url = f"https://www.youtube.com/embed/{vid}"
    image_url = f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"

    return video_url, image_url

# You can check by pass name and artists
# video_url, image_url = get_youtube_description("APT", "Rose")
#
# webbrowser.open(video_url)
#
# img = requests.get(image_url, stream=True).raw
# plt.imshow(Image.open(img))
# plt.axis('off')
# plt.show()