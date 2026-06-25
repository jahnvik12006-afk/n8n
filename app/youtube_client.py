from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.config import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def get_credentials() -> Credentials:
    return Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=SCOPES,
    )


def youtube_data_client():
    return build("youtube", "v3", credentials=get_credentials(), cache_discovery=False)


def youtube_analytics_client():
    return build("youtubeAnalytics", "v2", credentials=get_credentials(), cache_discovery=False)
