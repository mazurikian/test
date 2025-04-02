import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow

os.system('ffmpeg -i "https://stream.kick.com/ivs/v1/196233775518/V3f9DWwe2lks/2025/3/31/3/34/LHesGrlEamEZ/media/hls/master.m3u8" -c copy output.ts')

storage = Storage("oauth2.json")
credentials = storage.get()

if not credentials or credentials.invalid:
    flow = flow_from_clientsecrets("client_secret.json", "https://www.googleapis.com/auth/youtube.upload")
    credentials = run_flow(flow, storage)

youtube = build("youtube", "v3", credentials=credentials)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": "Educando La Adolfina",
            "description": "Video subido automáticamente.",
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    },
    media_body=MediaFileUpload("output.ts", mimetype='video/*')
)

request.execute()
