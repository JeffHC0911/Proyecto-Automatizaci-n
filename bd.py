import threading
import sqlite3

# Crear un Lock para sincronizar el acceso a la base de datos
db_lock = threading.Lock()

# Configurar base de datos SQLite (con check_same_thread=False para permitir acceso en varios hilos)
conn = sqlite3.connect('db/nivel_tanque.db', check_same_thread=False)
cursor = conn.cursor()

# Crear tabla si no existe
cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS lecturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_hora TEXT NOT NULL,
        nivel REAL NOT NULL,
        porcentaje REAL NOT NULL
    )
''')
conn.commit()

def save_to_db(fecha_hora, nivel, porcentaje):
    with db_lock:  # Asegura que solo un hilo acceda a la base de datos a la vez
        cursor.execute(''' 
            INSERT INTO lecturas (fecha_hora, nivel, porcentaje)
            VALUES (?, ?, ?)
        ''', (fecha_hora, nivel, porcentaje))
        conn.commit()

# Función para obtener todas las lecturas desde la base de datos
def get_all_readings():
    with db_lock:  # Asegura que solo un hilo acceda a la base de datos a la vez
        cursor.execute("SELECT * FROM lecturas ORDER BY fecha_hora DESC")
        rows = cursor.fetchall()
    return rows

def delete_old_data():
    with db_lock:  # Asegura que solo un hilo acceda a la base de datos a la vez
        cursor.execute("DELETE FROM lecturas WHERE fecha_hora < datetime('now', '-30 days')")
        conn.commit()  # Elimina datos más antiguos que 30 días (puedes cambiar el intervalo)
