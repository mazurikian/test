from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow

# Autenticación
storage = Storage("oauth2.json")
credentials = storage.get()
if not credentials or credentials.invalid:
    flow = flow_from_clientsecrets("client_secret.json", "https://www.googleapis.com/auth/youtube.upload")
    credentials = run_flow(flow, storage)

youtube = build("youtube", "v3", credentials=credentials)

# Configurar carga con fragmentación para evitar problemas de memoria
file_path = "output.ts"
media = MediaFileUpload(file_path, mimetype='video/*', chunksize=-1, resumable=True)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": "Vector | 02/04/2025",
            "description": "HOY EMPEZAMOS SERIE DE RAFT!!! Supervivencia en el mar 🌊🌊🌊  - !duelbits !kingslv !skinclub !crew - META SUBS: 103/110 https://kick.com/vector/videos/97f4321b-9ef0-4383-b8e8-9e9ad83c6308",
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
