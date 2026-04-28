import os
# Ruta relativa: desde app/edge/src/ → sube 2 niveles a app/ → data/drivesense.db
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'drivesense.db'))
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Definimos los nuevos prefijos de fecha
dates = ["20250707", "20250708", "20250709", "20250710"]

# Obtener los primeros 12 ids de la tabla infractions
cursor.execute("SELECT id, timestamp FROM infractions ORDER BY id ASC LIMIT 12;")
rows = cursor.fetchall()

# Actualizar los timestamps
for i, (row_id, old_timestamp) in enumerate(rows):
    new_prefix = dates[i // 3]
    suffix = old_timestamp.split('_')[1] if '_' in old_timestamp else '000000'
    new_timestamp = f"{new_prefix}_{suffix}"
    cursor.execute("UPDATE infractions SET timestamp = ? WHERE id = ?", (new_timestamp, row_id))
    print(f"Actualizado ID {row_id}: {old_timestamp} → {new_timestamp}")

# Guardar y cerrar
conn.commit()
conn.close()
