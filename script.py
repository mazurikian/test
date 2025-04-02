import os
import requests
import httplib2
import sys
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from tqdm import tqdm  # Librería para la barra de progreso

# Configuración de la API de YouTube
CLIENT_SECRETS_FILE = 'client_secrets.json'
YOUTUBE_READ_WRITE_SCOPE = 'https://www.googleapis.com/auth/youtube.upload'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
OAUTH2_STORAGE_FILE = 'oauth2.json'
VIDEO_URL = "https://archive.org/download/vector_twitcheducando-la-adolfina-con-frankkaster-coscu-y-la-chilena-2018-01-09T21_05_48Z/EDUCANDO%20LA%20ADOLFINA%20CON%20FRANKKASTER%2C%20COSCU%20Y%20LA%20CHILENA.ts"
OUTPUT_FILE = "output.ts"


def download_video(url, output_path):
    """Descarga un archivo desde una URL con barra de progreso."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as file, tqdm(
            desc="Descargando",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
            bar.update(len(chunk))
    print(f"\nVideo descargado como {output_path}")


def get_authenticated_service():
    """Autentica con la API de YouTube usando OAuth 2.0."""
    flow = flow_from_clientsecrets(
        CLIENT_SECRETS_FILE,
        scope=YOUTUBE_READ_WRITE_SCOPE,
        message="Descarga el archivo client_secrets.json de Google Cloud Console"
    )
    storage = Storage(OAUTH2_STORAGE_FILE)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=credentials.authorize(httplib2.Http()))


def upload_video(youtube, file_path, title, description, category_id='22', privacy_status='public', made_for_kids=False):
    """Sube un video a YouTube con barra de progreso."""
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': made_for_kids
        }
    }
    
    media_body = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True, mimetype='video/*')
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media_body)
    
    print("Subiendo video...")
    progress_bar = tqdm(total=os.path.getsize(file_path), unit='B', unit_scale=True, unit_divisor=1024)
    response = None
    
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress_bar.update(status.resumable_progress - progress_bar.n)
    progress_bar.close()
    
    print(f"\nVideo subido con ID: {response['id']}")
    return response['id']


if __name__ == '__main__':
    try:
        # Descargar el video
        download_video(VIDEO_URL, OUTPUT_FILE)
        
        # Autenticarse en YouTube
        youtube = get_authenticated_service()
        
        # Subir el video a YouTube
        video_title = 'Educando La Adolfina - Frankkaster, Coscu y La Chilena'
        video_description = 'Video descargado y subido automáticamente.'
        upload_video(youtube, OUTPUT_FILE, video_title, video_description, made_for_kids=False)
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}", file=sys.stderr)
