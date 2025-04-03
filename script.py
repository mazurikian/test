import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow

if len(sys.argv) < 3:
    print("Uso: python script.py <archivo> <sufijo_título>")
    sys.exit(1)

file_path = sys.argv[1]
title_suffix = sys.argv[2]

# Autenticación
storage = Storage("oauth2.json")
credentials = storage.get()
if not credentials or credentials.invalid:
    flow = flow_from_clientsecrets(
        "oauth2.json",
        scope="https://www.googleapis.com/auth/youtube.upload",
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    credentials = run_flow(flow, storage)

youtube = build("youtube", "v3", credentials=credentials)

# Configurar carga
media = MediaFileUpload(
    file_path,
    mimetype='video/*',
    chunksize=-1,
    resumable=True
)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": f"Vector | 01/04/2025 - {title_suffix}",
            "description": "HOY VENDEMOS DROGUITA RICA 🌿 + NUEVO JUEGO DE TERROR DE ASTRONAUTAS 🚀 - !duelbits !kingslv !skinclub !crew - META SUBS: 103/110 https://kick.com/vector/videos/97f4321b-9ef0-4383-b8e8-9e9ad83c6308",
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    },
    media_body=media
)

# Subida con seguimiento
response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print(f"Progreso: {status.progress() * 100:.2f}%")

print("Subida completada exitosamente!")
