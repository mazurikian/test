import json
import os
import subprocess
import re
import sys
from datetime import datetime
from internetarchive import upload, Item

def sanitize_identifier(title):
    # Convertir a minúsculas y reemplazar espacios con guiones
    identifier = title.lower()
    # Eliminar caracteres especiales excepto guiones
    identifier = re.sub(r'[^a-z0-9-]', '', identifier)
    # Limitar longitud a 80 caracteres
    return identifier[:80]

def generate_metadata(title):
    return {
        'title': title,
        'mediatype': 'movies',
        'collection': 'opensource',
        'subject': 'twitch;streaming;gameplay',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'language': 'Spanish',
        'description': f"VOD de Twitch: {title}"
    }

def download_vod(m3u8_url, output_filename):
    try:
        command = [
            'ffmpeg',
            '-i', m3u8_url,
            '-c', 'copy',
            output_filename
        ]
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error en FFmpeg: {e.stderr.decode('utf-8') if e.stderr else 'Error desconocido'}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python script.py <archivo_vods.json>")
        sys.exit(1)
    
    json_filename = sys.argv[1]
    try:
        with open(json_filename, 'r', encoding='utf-8') as f:
            vods = json.load(f)
    except FileNotFoundError:
        print(f"Archivo '{json_filename}' no encontrado.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"El archivo '{json_filename}' no contiene un JSON válido.")
        sys.exit(1)
    
    os.makedirs('downloads', exist_ok=True)
    
    for vod in vods:
        title = vod.get('title')
        url = vod.get('url')
        if not title or not url:
            print("VOD sin título o URL, omitiendo...")
            continue
        
        # Generar campos automáticamente
        identifier = f"vector-twitch-{sanitize_identifier(title)}-{datetime.now().strftime('%Y%m%d')}"
        metadata = generate_metadata(title)
        
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_filename = f"downloads/{safe_title}.ts"  # Cambiado a .mp4 para mejor compatibilidad
        
        print(f"\nProcesando: {title}")
        print(f"Identifier: {identifier}")
        
        # Obtener URL real con yt-dlp
        print("Obteniendo URL del stream...")
        try:
            get_url_cmd = ['yt-dlp', '-g', '-f', 'best', url]
            result = subprocess.run(get_url_cmd, capture_output=True, text=True, check=True)
            m3u8_url = result.stdout.strip()
            print("URL real obtenida")
        except subprocess.CalledProcessError as e:
            print(f"Error al obtener URL: {e.stderr if e.stderr else 'Error desconocido'}")
            continue
        
        # Descargar con FFmpeg
        if download_vod(m3u8_url, output_filename):
            print("Descarga completada. Subiendo a Internet Archive...")
            try:
                item = upload(
                    identifier,
                    files=[output_filename],
                    metadata=metadata,
                    retries=5,
                    verbose=True
                )
                print(f"Subida exitosa: https://archive.org/details/{identifier}")
                os.remove(output_filename)
                print("Archivo local eliminado")
            except Exception as e:
                print(f"Error al subir a Internet Archive: {str(e)}")
        else:
            print("Error en la descarga, omitiendo subida")

if __name__ == "__main__":
    main()
