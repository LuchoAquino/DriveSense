
import sqlite3
import os

# Ruta al archivo DB: sube 2 niveles desde app/backend/app/ hasta app/, luego entra a data/
DATABASE_URL = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'drivesense.db')

def get_db_connection():
    """
    Crea y devuelve un objeto de conexión a la base de datos SQLite.
    La conexión se configura para devolver filas que actúan como diccionarios,
    lo que facilita el acceso a los datos por nombre de columna.
    """
    if not os.path.exists(DATABASE_URL):
        raise FileNotFoundError(f"El archivo de la base de datos no se encontró en {DATABASE_URL}")
        
    try:
        conn = sqlite3.connect(DATABASE_URL)
        # Configura la conexión para que las filas devueltas sean objetos de tipo sqlite3.Row
        # Esto permite acceder a las columnas por su nombre, como en un diccionario.
        # Ejemplo: row['plate_number'] en lugar de row[2]
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None
