import json
import os
import re
import subprocess
import sys
import requests
import unicodedata
from datetime import datetime
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

# Extrae la fecha de subida (uploadDate) del contenido HTML de la URL.
def get_upload_date(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            html_text = response.text

            # Primera estrategia: Buscar JSON-LD que contenga "uploadDate"
            json_ld_matches = re.findall(
                r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
                html_text,
                re.DOTALL
            )
            for json_ld in json_ld_matches:
                try:
                    data = json.loads(json_ld)
                    # Si es una lista de metadatos, recorrer cada uno
                    if isinstance(data, list):
                        for entry in data:
                            if isinstance(entry, dict) and entry.get("uploadDate"):
                                return entry["uploadDate"]
                    elif isinstance(data, dict):
                        if data.get("uploadDate"):
                            return data["uploadDate"]
                except Exception:
                    # Si no se pudo parsear el JSON, se ignora y se sigue con la siguiente estrategia.
                    pass

            # Segunda estrategia: Buscar mediante regex directa en el HTML
            matches = re.findall(r'"uploadDate"\s*:\s*"([^"]+)"', html_text)
            if matches:
                return matches[0]
    except Exception as e:
        print(f"Error al obtener la fecha de subida desde {url}: {e}")

    # Fallback: Si no se encuentra, se utiliza la fecha/hora actual
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# Genera un diccionario de metadatos usando el título y la URL.
def create_metadata(title, url):
    return {
        "title": title,
        "mediatype": "movies",
        "collection": "opensource_movies"
    }

# Descarga el archivo de video usando ffmpeg, mostrando solo advertencias y errores.
def download_video(m3u8_url, filename):
    subprocess.run(
        ["ffmpeg", "-loglevel", "warning", "-i", m3u8_url, "-c", "copy", filename],
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

# Procesa cada video (VOD) de forma independiente.
def process_video(video):
    title = video.get("title")
    url = video.get("url")
    if not title or not url:
        return

    output_filename = title + ".ts"
    base_identifier = "twitch-" + create_identifier(title)
    
    # Cada URL se procesa de forma independiente para obtener su uploadDate.
    upload_date = get_upload_date(url)
    # Se reemplazan caracteres problemáticos en la fecha.
    safe_date = upload_date.replace(":", "_")
    identifier = f"{base_identifier}-{safe_date}"
    
    metadata = create_metadata(title, url)
    m3u8_url = get_stream_url(url)

    print(f"ID Video: https://archive.org/details/{identifier}")
    
    # Descarga el video utilizando ffmpeg.
    download_video(m3u8_url, output_filename)
    print(f"Descarga completada: {output_filename}")
    
    print("Iniciando la subida a Internet Archive...")
    upload_result = upload(
        identifier,
        files=[output_filename],
        metadata=metadata,
        retries=5,
        verbose=True
    )
    
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
    
    # Se procesa cada video de forma independiente.
    for video in videos:
        process_video(video)

if __name__ == "__main__":
    main()
