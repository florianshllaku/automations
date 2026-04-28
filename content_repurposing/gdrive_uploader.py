import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent / "token.json"
DRIVE_FOLDER_NAME = "TikTok Videos"


def _get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service) -> str:
    """Return the ID of the TikTok Videos folder, creating it if needed."""
    query = (
        f"name='{DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    folder_metadata = {
        "name": DRIVE_FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    print(f"  Created Google Drive folder '{DRIVE_FOLDER_NAME}'")
    return folder["id"]


def upload_video(video_path: str) -> str:
    """
    Upload a video file to the TikTok Videos folder on Google Drive.
    Makes it publicly accessible and returns a direct-download URL.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    print(f"  Authenticating with Google Drive ...")
    service = _get_service()

    print(f"  Locating '{DRIVE_FOLDER_NAME}' folder ...")
    folder_id = _get_or_create_folder(service)

    print(f"  Uploading {video_path.name} ...")
    file_metadata = {
        "name": video_path.name,
        "parents": [folder_id],
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name",
    ).execute()

    file_id = uploaded["id"]

    # Make the file publicly accessible
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    print(f"  Uploaded: {video_path.name}")
    print(f"  Public URL: {direct_url}")
    return direct_url


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python gdrive_uploader.py <path_to_video.mp4>")
        sys.exit(1)
    url = upload_video(sys.argv[1])
    print(f"\nDone! Share URL:\n{url}")
