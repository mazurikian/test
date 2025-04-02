import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow

os.system('ffmpeg -i "https://stream.kick.com/ivs/v1/196233775518/V3f9DWwe2lks/2025/4/1/16/15/JwdvOAppHrfG/media/hls/master.m3u8" -c copy output.ts')

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
            "title": "(01/04/2025)",
            "description": "HOY VENDEMOS DROGUITA RICA 🌿 + NUEVO JUEGO DE TERROR DE ASTRONAUTAS 🚀  - !duelbits !kingslv !skinclub !crew - META SUBS: 103/110 https://kick.com/vector/videos/97f4321b-9ef0-4383-b8e8-9e9ad83c6308",
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
