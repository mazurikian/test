from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow
import sys

def upload_video(file_path, title, description):
    # Autenticación
    storage = Storage("oauth2.json")
    credentials = storage.get()
    if not credentials or credentials.invalid:
        flow = flow_from_clientsecrets("client_secret.json", "https://www.googleapis.com/auth/youtube.upload")
        credentials = run_flow(flow, storage)

    youtube = build("youtube", "v3", credentials=credentials)

    # Configurar carga con fragmentación para evitar problemas de memoria
    media = MediaFileUpload(file_path, mimetype='video/*', chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=media
    )

    # Subir en partes
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progreso: {status.progress() * 100:.2f}%")

    print("Subida completada.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <file_path> <title> <description>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3]
    
    upload_video(file_path, title, description)
