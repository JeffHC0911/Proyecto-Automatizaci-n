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
        timestamp TEXT NOT NULL,
        water_level REAL NOT NULL,
        tank_percentage REAL NOT NULL,
        rain_humidity REAL NOT NULL
    )
''')
conn.commit()

# Función para guardar los datos en la base de datos
def save_to_db(timestamp, water_level, tank_percentage, rain_humidity):
    # Aquí debes agregar la lógica para guardar los datos, incluyendo la humedad del sensor de lluvia
    query = """
        INSERT INTO lecturas (timestamp, water_level, tank_percentage, rain_humidity)
        VALUES (?, ?, ?, ?)
    """
    params = (timestamp, water_level, tank_percentage, rain_humidity)
    # Ejecutar el query en la base de datos
    cursor.execute(query, params)
    conn.commit()


# Función para obtener todas las lecturas desde la base de datos
def get_all_readings():
    with db_lock:  # Asegura que solo un hilo acceda a la base de datos a la vez
        cursor.execute("SELECT * FROM lecturas ORDER BY timestamp DESC")
        rows = cursor.fetchall()
    return rows

def delete_old_data():
    with db_lock:  # Asegura que solo un hilo acceda a la base de datos a la vez
        cursor.execute("DELETE FROM lecturas WHERE timestamp < datetime('now', '-30 days')")
        conn.commit()  # Elimina datos más antiguos que 30 días (puedes cambiar el intervalo)
