import json
import os
import re
import subprocess
import sys
import requests
import unicodedata
from internetarchive import upload

# Elimina acentos y caracteres especiales del texto.
def normalize_text(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

# Crea un identificador a partir del título.
def create_identifier(title):
    text = normalize_text(title).lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    identifier = re.sub(r'\s+', '-', text)
    return identifier

# Busca en la página la fecha de subida (uploadDate)
def get_upload_date(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            match = re.search(r'"uploadDate"\s*:\s*"([^"]+)"', response.text)
            if match:
                return match.group(1)
    except Exception as e:
        print("Error al obtener la fecha de subida desde", url, ":", e)
    return None

# Genera un diccionario de metadatos usando el título y la URL.
def create_metadata(title, url):
    return {
        "title": title,
        "mediatype": "movies",
        "collection": "opensource_movies"
    }

# Descarga el archivo de video usando ffmpeg, mostrando advertencias y errores.
def download_video(m3u8_url, filename):
    subprocess.run(
        ["ffmpeg", "-i", m3u8_url, "-c", "copy", filename],
        check=True
    )
    return True

# Obtiene la URL directa del stream usando yt-dlp.
def get_stream_url(url):
    result = subprocess.run(
        ["yt-dlp", "-g", "-f", "best", url],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

# Procesa cada video (VOD) con la información provista.
def process_video(video):
    title = video.get("title")
    url = video.get("url")
    if not title or not url:
        return

    output_filename = title + ".ts"
    # Agrega el prefijo "twitch-" al identificador del título.
    identifier = "twitch-" + create_identifier(title)
    
    # Intenta obtener la fecha de subida y la incorpora al identificador.
    upload_date = get_upload_date(url)
    if upload_date:
        safe_date = upload_date.replace(":", "_")
        identifier = identifier + "-" + safe_date

    metadata = create_metadata(title, url)
    m3u8_url = get_stream_url(url)

    print(f"ID Video: https://archive.org/details/{identifier}")
    
    # Descarga el video utilizando ffmpeg; se muestran advertencias y errores en la consola.
    download_video(m3u8_url, output_filename)
    print(f"Descarga completada: {output_filename}")
    
    print("Iniciando la subida a Internet Archive...")
    # Sube el video a Internet Archive de manera silenciosa.
    upload_result = upload(
        identifier,
        files=[output_filename],
        metadata=metadata,
        retries=5,
        verbose=True
    )
    
    # Una vez subido, se muestra en pantalla el enlace de los detalles.
    print(f"Video subido correctamente: https://archive.org/details/{identifier}")
    
    # Elimina el archivo descargado localmente.
    os.remove(output_filename)

# Función principal que carga la lista de videos y los procesa.
def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: script.py <archivo_json>")
    
    json_file = sys.argv[1]
    with open(json_file, "r", encoding="utf-8") as f:
        videos = json.load(f)
    
    for video in reversed(videos):
        process_video(video)

if __name__ == "__main__":
    main()
