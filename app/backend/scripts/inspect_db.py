import sqlite3
import os

# Construimos la ruta al archivo de la base de datos, que está en el directorio raíz del proyecto.
# Sube 3 niveles desde app/backend/scripts/ hasta app/, luego entra a data/
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'drivesense.db')

def inspect_database(db_path):
    """
    Se conecta a la base de datos SQLite especificada e imprime el esquema de cada tabla.
    """
    if not os.path.exists(db_path):
        print(f"Error: El archivo de la base de datos no se encontró en la ruta: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Obtener la lista de todas las tablas en la base de datos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("La base de datos no contiene tablas.")
            return

        print(f"--- ESQUEMA DE LA BASE DE DATOS '{os.path.basename(db_path)}' ---")

        # Para cada tabla, obtener y mostrar la información de sus columnas
        for table_name_tuple in tables:
            table_name = table_name_tuple[0]
            print(f"\n[+] Tabla: {table_name}")

            # PRAGMA table_info() devuelve una fila por cada columna en la tabla
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            # Imprimir encabezados de la tabla de esquema
            print(f"{'ID':<5} {'Nombre':<25} {'Tipo':<15} {'No Nulo':<10} {'Default':<15} {'PK':<5}")
            print("-" * 80)

            # Imprimir detalles de cada columna
            for col in columns:
                col_id, name, col_type, not_null, default_val, is_pk = col
                print(f"{str(col_id):<5} {name:<25} {col_type:<15} {str(bool(not_null)):<10} {str(default_val):<15} {str(bool(is_pk)):<5}")

    except sqlite3.Error as e:
        print(f"Ocurrió un error de SQLite: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    inspect_database(DB_PATH)
