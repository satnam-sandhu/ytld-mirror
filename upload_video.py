import os
import sys
import argparse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Define the scopes
# We need upload permission
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    """
    Handles OAuth2 authentication and returns a YouTube service object.
    Expects client_secret.json to be present in the same directory.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens
    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')
    secret_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secret.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(secret_path):
                print(f"Error: {secret_path} not found.")
                print("Please download your client_secret.json from Google Cloud Console and place it in the script directory.")
                sys.exit(1)
                
            flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    return build('youtube', 'v3', credentials=creds)

def upload_video(video_file, title, description, category_id="22", privacy_status="public"):
    """
    Uploads a video to YouTube.
    """
    youtube = get_authenticated_service()
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': category_id,
            'tags': ['Shorts'] if "shorts" in title.lower() else []
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }
    
    print(f"Uploading video: {video_file}")
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    
    try:
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
        
        print(f"Upload successful! Video ID: {response['id']}")
        return response['id']
    except Exception as e:
        print(f"An error occurred during upload: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument("file", help="Path to the video file")
    parser.add_argument("--title", help="Title of the video", default="New Short")
    parser.add_argument("--description", help="Description of the video", default="Uploaded via automated script")
    parser.add_argument("--category", help="Category ID (default: 22 for People & Blogs)", default="22")
    parser.add_argument("--privacy", help="Privacy status (public, private, unlisted)", default="public")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} does not exist.")
        sys.exit(1)
        
    upload_video(args.file, args.title, args.description, args.category, args.privacy)

if __name__ == "__main__":
    main()
