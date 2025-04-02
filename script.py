import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow

# Descargar el video con ffmpeg
video_url = "https://stream.kick.com/ivs/v1/196233775518/V3f9DWwe2lks/2025/3/31/3/34/LHesGrlEamEZ/media/hls/master.m3u8"
output_file = "output.ts"
os.system(f'ffmpeg -i "{video_url}" -c copy {output_file}')

# Cargar credenciales de YouTube
storage = Storage("oauth2.json")
credentials = storage.get()

if not credentials or credentials.invalid:
    flow = flow_from_clientsecrets("client_secrets.json", "https://www.googleapis.com/auth/youtube.upload")
    credentials = run_flow(flow, storage)

# Subir el video a YouTube
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
    media_body=MediaFileUpload(output_file, mimetype='video/*')
)

request.execute()
