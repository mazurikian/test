import os
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from oauth2client.client import flow_from_clientsecrets
from tqdm import tqdm

# Configuración de la API de YouTube
CLIENT_SECRETS_FILE = 'client_secrets.json'
OAUTH2_STORAGE_FILE = 'oauth2.json'
YOUTUBE_SCOPE = 'https://www.googleapis.com/auth/youtube.upload'
YOUTUBE_SERVICE_NAME = 'youtube'
YOUTUBE_VERSION = 'v3'
VIDEO_URL = "https://stream.kick.com/ivs/v1/196233775518/V3f9DWwe2lks/2025/3/31/3/34/LHesGrlEamEZ/media/hls/master.m3u8"
OUTPUT_FILE = "output.ts"

def download_video(m3u8_url, output_file):
    """Descarga un video desde un enlace M3U8 usando ffmpeg y muestra el progreso."""
    cmd = ["ffmpeg", "-i", m3u8_url, "-c", "copy", output_file]
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
    with tqdm(unit="B", unit_scale=True, desc="Descargando video") as progress:
        for line in process.stderr:
            if "frame=" in line:
                progress.update(1)
    process.wait()
    if process.returncode != 0:
        raise Exception("Error en la descarga con ffmpeg")
    print(f"Video descargado: {output_file}")

def authenticate_youtube():
    """Autentica y devuelve un servicio de YouTube."""
    storage = Storage(OAUTH2_STORAGE_FILE)
    credentials = storage.get() or run_flow(
        flow_from_clientsecrets(CLIENT_SECRETS_FILE, YOUTUBE_SCOPE), storage)
    return build(YOUTUBE_SERVICE_NAME, YOUTUBE_VERSION, credentials=credentials)

def upload_video(youtube, file_path, title, description, category_id='22', privacy='public'):
    """Sube un video a YouTube."""
    request = youtube.videos().insert(
        part='snippet,status',
        body={
            'snippet': {'title': title, 'description': description, 'categoryId': category_id},
            'status': {'privacyStatus': privacy, 'selfDeclaredMadeForKids': False}
        },
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype='video/*')
    )
    response = request.execute()
    print(f"Video subido con ID: {response['id']}")
    return response['id']

if __name__ == '__main__':
    try:
        download_video(VIDEO_URL, OUTPUT_FILE)
        youtube = authenticate_youtube()
        upload_video(youtube, OUTPUT_FILE, 'Educando La Adolfina', 'Video subido automáticamente.')
    except Exception as e:
        print(f"Error: {e}")
