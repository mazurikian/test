import json
import os
import re
import subprocess
import sys
import requests
import unicodedata
from datetime import datetime
from internetarchive import upload

def normalize_text(text):
    """
    Devuelve una versión normalizada del texto para uso en nombres de archivo en el sistema.
    Se elimina o reemplaza caracteres que puedan causar problemas en ffmpeg.
    """
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

def create_identifier(title):
    """
    Crea un identificador a partir del título usando la versión normalizada (en minúsculas) y
    reemplazando espacios por guiones.
    """
    text = normalize_text(title).lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'\s+', '-', text)

def get_upload_date(url):
    """
    Extrae la fecha de subida (uploadDate) del HTML de la URL.
    Primero intenta obtenerla desde bloques JSON-LD, y si falla, mediante regex.
    Si no se encuentra, retorna la fecha/hora actual.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            html_text = response.text

            # Primera estrategia: Buscar bloque JSON-LD con "uploadDate"
            json_ld_matches = re.findall(
                r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
                html_text,
                re.DOTALL
            )
            for json_ld in json_ld_matches:
                try:
                    data = json.loads(json_ld)
                    if isinstance(data, list):
                        for entry in data:
                            if isinstance(entry, dict) and entry.get("uploadDate"):
                                return entry["uploadDate"]
                    elif isinstance(data, dict) and data.get("uploadDate"):
                        return data["uploadDate"]
                except Exception:
                    pass

            # Segunda estrategia: regex directa en el HTML
            matches = re.findall(r'"uploadDate"\s*:\s*"([^"]+)"', html_text)
            if matches:
                return matches[0]
    except Exception as e:
        print(f"Error al obtener la fecha desde {url}: {e}")
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def create_metadata(title, url):
    """
    Genera el diccionario de metadatos para Internet Archive usando EL título ORIGINAL.
    """
    return {
        "title": title,  # Título original del video
        "mediatype": "movies",
        "collection": "opensource_movies"
    }

def download_video(m3u8_url, filename):
    """
    Descarga el video usando ffmpeg hacia el archivo 'filename'.
    Se utiliza el log level "warning" para reducir la salida innecesaria.
    """
    subprocess.run(
        ["ffmpeg", "-loglevel", "warning", "-i", m3u8_url, "-c", "copy", filename],
        check=True
    )
    return True

def get_stream_url(url):
    """
    Obtiene la URL directa del stream usando yt-dlp.
    """
    result = subprocess.run(
        ["yt-dlp", "-g", "-f", "best", url],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def get_upload_filename(title):
    """
    Retorna el nombre de archivo que se usará para subir el video.
    Se utiliza el título original agregando la extensión ".ts".
    Se reemplaza el caracter "/" (no permitido en nombres de archivo) por una barra similar "∕".
    """
    return title.replace("/", "∕") + ".ts"

def process_video(video):
    title = video.get("title")
    url = video.get("url")
    if not title or not url:
        return

    # Para la descarga, se usa un nombre de archivo "seguro"
    safe_filename = normalize_text(title) + ".ts"
    # Permitir que en la subida se use el nombre "original" (con solo el reemplazo de "/" por "∕")
    upload_filename = get_upload_filename(title)
    
    base_identifier = "twitch-" + create_identifier(title)
    upload_date = get_upload_date(url)
    safe_date = upload_date.replace(":", "_")
    identifier = f"{base_identifier}-{safe_date}"

    metadata = create_metadata(title, url)
    m3u8_url = get_stream_url(url)

    print(f"ID Video: https://archive.org/details/{identifier}")

    # Descargamos usando el nombre de archivo seguro
    download_video(m3u8_url, safe_filename)
    print(f"Descarga completada: {safe_filename}")

    # Renombramos para que el archivo que se suba sea el original
    if safe_filename != upload_filename:
        os.rename(safe_filename, upload_filename)

    print("Iniciando la subida a Internet Archive...")
    upload_result = upload(
        identifier,
        files=[upload_filename],
        metadata=metadata,
        retries=5,
        verbose=True
    )

    print(f"Video subido correctamente: https://archive.org/details/{identifier}")
    os.remove(upload_filename)

def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: script.py <archivo_json>")
    
    json_file = sys.argv[1]
    with open(json_file, "r", encoding="utf-8") as f:
        videos = json.load(f)

    for video in videos:
        process_video(video)

if __name__ == "__main__":
    main()
