import os
import requests
from dotenv import load_dotenv
from logger import log

load_dotenv()

BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
TIKTOK_CHANNEL_ID = "69eb46c4031bfa423c3a9d93"
GRAPHQL_ENDPOINT = "https://api.bufferapp.com/graphql"

MUTATION = """
mutation CreatePost($input: PostCreateInput!) {
  postCreate(input: $input) {
    post {
      id
      status
      dueAt
    }
    errors {
      message
    }
  }
}
"""


def post_video_to_tiktok(video_url: str, title: str) -> dict:
    """
    Post a video to TikTok via Buffer.
    video_url: publicly accessible URL (e.g. Google Drive direct link)
    title: caption / title for the post
    Returns the created post dict.
    """
    if not BUFFER_API_KEY:
        raise ValueError("BUFFER_API_KEY is not set in .env")

    variables = {
        "input": {
            "channelId": TIKTOK_CHANNEL_ID,
            "text": title,
            "schedulingType": "automatic",
            "shareMode": "addToQueue",
            "assets": {
                "videos": [
                    {
                        "url": video_url,
                        "metadata": {"title": title},
                    }
                ]
            },
            "metadata": {
                "tiktok": {"title": title}
            },
        }
    }

    headers = {
        "Authorization": f"Bearer {BUFFER_API_KEY}",
        "Content-Type": "application/json",
    }

    log(f"Posting to TikTok via Buffer — title: {title}, url: {video_url}")
    response = requests.post(
        GRAPHQL_ENDPOINT,
        json={"query": MUTATION, "variables": variables},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    errors = data.get("data", {}).get("postCreate", {}).get("errors", [])
    if errors:
        raise RuntimeError(f"Buffer API errors: {errors}")

    post = data.get("data", {}).get("postCreate", {}).get("post", {})
    log(f"TikTok post queued — id: {post.get('id')}, dueAt: {post.get('dueAt')}")
    return post
