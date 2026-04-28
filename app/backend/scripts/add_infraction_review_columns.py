import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'drivesense.db')

def add_columns_to_infractions_table():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Add review_decision column
        try:
            cursor.execute("ALTER TABLE infractions ADD COLUMN review_decision TEXT;")
            print("Column 'review_decision' added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'review_decision' already exists.")
            else:
                raise

        # Add review_comments column
        try:
            cursor.execute("ALTER TABLE infractions ADD COLUMN review_comments TEXT;")
            print("Column 'review_comments' added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'review_comments' already exists.")
            else:
                raise

        # Add reviewed_at column
        try:
            cursor.execute("ALTER TABLE infractions ADD COLUMN reviewed_at TEXT;")
            print("Column 'reviewed_at' added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column 'reviewed_at' already exists.")
            else:
                raise

        conn.commit()
        print("Database schema updated successfully.")

    except sqlite3.Error as e:
        print(f"Error al actualizar el esquema de la base de datos: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_columns_to_infractions_table()
