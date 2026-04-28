import sqlite3
import os
import json

# Raíz de app/ (2 niveles arriba de app/edge/src/)
app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(app_root, 'data', 'drivesense.db')

def init_db():
    """
    Inicializa la base de datos SQLite, creando las tablas necesarias y poblándolas
    con datos iniciales si no existen. NO elimina datos existentes.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Crear tabla camera_groups solo si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS camera_groups (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL
        );
        """)

        # Crear tabla cameras solo si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            camera_group_id INTEGER,
            FOREIGN KEY (camera_group_id) REFERENCES camera_groups(id)
        );
        """)

        # Crear tabla rules solo si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        """)

        # Crear tabla infractions solo si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS infractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            plate_number TEXT NOT NULL,
            camera_id INTEGER NOT NULL,
            rule_id INTEGER, -- Clave foránea a rules.id
            confidence REAL,
            status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
            image_path TEXT NOT NULL,
            video_path TEXT NOT NULL,
            thumbnail_path TEXT NOT NULL,
            review_decision TEXT,
            review_comments TEXT,
            reviewed_at TEXT,
            FOREIGN KEY (camera_id) REFERENCES cameras(id),
            FOREIGN KEY (rule_id) REFERENCES rules(id)
        );
        """)

        # Insertar datos fijos solo si no existen
        cursor.execute("SELECT COUNT(*) FROM camera_groups WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO camera_groups (id, name, city) VALUES (?, ?, ?);", (1, "Rimac", "Lima"))
        
        cursor.execute("SELECT COUNT(*) FROM cameras WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO cameras (id, name, latitude, longitude, camera_group_id) VALUES (?, ?, ?, ?, ?);", (1, "CAM001", -12.023144, -77.049956, 1))
        
        # Insertar reglas solo si no existen
        rules_data = [
            (1, "Exceso_de_velocidad"),
            (2, "Semaforo_Rojo"),
            (3, "Invasion_Cruce_Peatonal"),
        ]
        for rule_id, rule_name in rules_data:
            cursor.execute("SELECT COUNT(*) FROM rules WHERE id = ?", (rule_id,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO rules (id, name) VALUES (?, ?);", (rule_id, rule_name))

        conn.commit()
        conn.close()
        
        print(f"[INFO] Base de datos inicializada correctamente en: {DB_PATH}")

    except sqlite3.Error as e:
        print(f"[ERROR] Ocurrió un error al inicializar la base de datos: {e}")

def save_infraction_metadata(timestamp, plate_number, camera_id, rule_id, confidence, image_path, video_path, thumbnail_path):
    """
    Guarda la metadata de una infracción en la base de datos SQLite.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO infractions (timestamp, plate_number, camera_id, rule_id, confidence, image_path, video_path, thumbnail_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        
        # Extraer solo los nombres de archivo de las rutas
        image_filename = os.path.basename(image_path)
        video_filename = os.path.basename(video_path)
        thumbnail_filename = os.path.basename(thumbnail_path)

        data_tuple = (timestamp, plate_number, camera_id, rule_id, confidence, image_filename, video_filename, thumbnail_filename)
        
        cursor.execute(insert_query, data_tuple)
        
        conn.commit()
        conn.close()
        
        print(f"[INFO] Metadata de la infracción para la placa {plate_number} guardada en la base de datos.")

    except sqlite3.Error as e:
        print(f"[ERROR] Ocurrió un error al guardar la metadata en la base de datos: {e}")

def get_all_rules():
    """
    Obtiene todas las reglas de infracción de la base de datos.
    Returns:
        list: Una lista de diccionarios, donde cada diccionario representa una regla
              con 'id' y 'name'.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM rules;")
        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rules
    except sqlite3.Error as e:
        print(f"[ERROR] Error al obtener reglas de la base de datos: {e}")
        return []

def export_infractions_to_json():
    """
    Exporta todos los registros de infracciones desde la base de datos SQLite a un archivo JSON.
    El archivo JSON se guardará en la raíz del proyecto.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM infractions")
        rows = cursor.fetchall()
        
        infractions_list = []
        for row in rows:
            infractions_list.append(dict(row)) # Convierte cada fila en un diccionario

        json_output_path = os.path.join(app_root, 'data', 'metadata.json')
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(infractions_list, f, ensure_ascii=False, indent=4)
        
        conn.close()
        print(f"[INFO] Metadata de infracciones exportada a: {json_output_path}")

    except sqlite3.Error as e:
        print(f"[ERROR] Ocurrió un error al exportar la metadata a JSON: {e}")
    except Exception as e:
        print(f"[ERROR] Ocurrió un error inesperado al exportar a JSON: {e}")

if __name__ == '__main__':
    # Este bloque permite ejecutar el script directamente para crear la base de datos
    print("Inicializando la base de datos para DriveSense...")
    init_db()