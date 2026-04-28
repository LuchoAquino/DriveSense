import os
import subprocess

# Ruta a tu carpeta de videos
EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'infractions_evidence'))


print(f"[INFO] Directorio de evidencias: {EVIDENCE_DIR}")
def reencode_to_h264(input_path, output_path):
    command = [
        'ffmpeg',
        '-y',  # Sobrescribir sin preguntar
        '-i', input_path,
        '-vcodec', 'libx264',
        '-acodec', 'aac',
        '-strict', 'experimental',
        output_path
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Falló la conversión de {input_path}")
        return False

def reencode_all_videos():
    print(f"[INFO] Procesando carpeta: {EVIDENCE_DIR}")
    for filename in os.listdir(EVIDENCE_DIR):
        if filename.endswith('.mp4') and not filename.endswith('_original_backup.mp4'):
            original_path = os.path.join(EVIDENCE_DIR, filename)
            temp_output = os.path.join(EVIDENCE_DIR, f"temp_h264.mp4")
            backup_path = os.path.join(EVIDENCE_DIR, f"{filename[:-4]}_original_backup.mp4")

            print(f"🔄 Reencodificando: {filename}...")
            success = reencode_to_h264(original_path, temp_output)
            if success:
                os.rename(original_path, backup_path)
                os.rename(temp_output, original_path)
                print(f"✅ Reemplazado con versión compatible: {filename}")
            else:
                print(f"❌ Falló la conversión de: {filename}")

    print("[✔] Finalizado")

if __name__ == '__main__':
    reencode_all_videos()
