
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'drivesense.db')

def insert_infraction():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO infractions (timestamp, plate_number, camera_id, rule_id, confidence, status, image_path, video_path, thumbnail_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ('20250709_100000', 'ABC-123', 1, 1, 0.95, 'PENDING_REVIEW', 'path/to/image.jpg', 'path/to/video.mp4', 'path/to/thumbnail.jpg')
        )
        conn.commit()
        print("Infracción de prueba insertada exitosamente.")
    except sqlite3.Error as e:
        print(f"Error al insertar infracción: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insert_infraction()
