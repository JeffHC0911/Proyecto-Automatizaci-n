import tkinter as tk
import serial
import threading
import time

from tkinter import ttk
from bd import save_to_db


# Configuración del puerto serial para Arduino
arduino_port = 'COM4'  # Cambia esto según tu sistema
arduino = serial.Serial(port=arduino_port, baudrate=9600, timeout=1)

# Función para actualizar los datos del tanque
def update_tank_display(tank_percentage, water_level, tank_status):
    # Actualizar los valores de los widgets
    tank_level.set(f"{water_level} cm")
    humidity_level.set(f"{tank_percentage}%")
    leak_sensor.set(tank_status)

    # Dibuja el nivel de agua
    canvas.delete("water")  # Borra el agua anterior
    water_height = (tank_percentage / 100) * 200
    canvas.create_rectangle(50, 200 - water_height, 150, 200, fill="blue", tags="water")
    
    # Cambiar el color del contorno según el nivel del tanque
    if tank_percentage >= 90:
        canvas.itemconfig(tank_outline, outline="red", width=3)
    elif tank_percentage >= 70:
        canvas.itemconfig(tank_outline, outline="yellow", width=3)
    else:
        canvas.itemconfig(tank_outline, outline="green", width=3)

# Función que lee datos del puerto serial (de Arduino)
def read_arduino_data():
    while True:
        try:
            if arduino.in_waiting > 0:
                line = arduino.readline().decode('utf-8').strip()  # Leer línea desde el Arduino
                if line:
                    # Suponemos que los datos están en el formato: "Nivel de agua: <nivel> cm (<porcentaje>%) - <estado>"
                    if "Nivel de agua:" in line:
                        # Extraemos el nivel de agua, porcentaje y el estado
                        parts = line.split(" ")
                        water_level = float(parts[3])  # Nivel en cm
                        tank_percentage = float(parts[5][1:-2])  # Porcentaje
                        tank_status = " ".join(parts[7:])  # El estado del tanque

                        # Obtener la fecha y hora actual
                        fecha_hora = time.strftime("%Y-%m-%d %H:%M:%S")

                        # Guardar los datos en la base de datos
                        save_to_db(fecha_hora, water_level, tank_percentage)
                        
                        # Actualiza la interfaz gráfica con los nuevos datos
                        update_tank_display(tank_percentage, water_level, tank_status)
        except Exception as e:
            print(f"Error leyendo datos del Arduino: {e}")

# Función para mostrar la pantalla principal
def show_main_screen():
    # Limpiar widgets anteriores
    for widget in main_frame.winfo_children():
        widget.pack_forget()

    # Canvas para mostrar el gráfico del tanque
    global canvas
    canvas = tk.Canvas(main_frame, width=200, height=250, bg="white")
    canvas.pack(pady=20)

    global tank_outline
    tank_outline = canvas.create_rectangle(50, 0, 150, 200, outline="black", width=2)

    # Pantalla principal
    tk.Label(main_frame, text="Nivel del Tanque:", font=("Arial", 14)).pack()
    tk.Label(main_frame, textvariable=tank_level, font=("Arial", 12)).pack(pady=5)
    tk.Label(main_frame, text="Porcentaje de Llenado:", font=("Arial", 14)).pack()
    tk.Label(main_frame, textvariable=humidity_level, font=("Arial", 12)).pack(pady=5)
    tk.Label(main_frame, text="Estado del Tanque:", font=("Arial", 14)).pack()
    tk.Label(main_frame, textvariable=leak_sensor, font=("Arial", 12)).pack(pady=5)

    # Botón para ver tabla y estadísticas
    ttk.Button(main_frame, text="Ver Tabla y Estadísticas", command=show_table).pack(pady=10)

# Función para mostrar la tabla de datos históricos
# Función para mostrar la tabla de datos históricos
def show_table():
    for widget in main_frame.winfo_children():
        widget.pack_forget()  # Oculta widgets en lugar de destruirlos

    # Crear tabla
    table = ttk.Treeview(main_frame, columns=("Fecha", "Nivel del Tanque", "Humedad", "Estado"), show="headings")
    table.heading("Fecha", text="Fecha")
    table.heading("Nivel del Tanque", text="Nivel del Tanque (cm)")
    table.heading("Humedad", text="Porcentaje (%)")
    table.heading("Estado", text="Estado")

    # Obtener los datos desde la base de datos
    from bd import get_all_readings  # Asegúrate de importar la función
    data = get_all_readings()  # Llama a la función que obtiene las lecturas

    # Insertar los datos obtenidos en la tabla
    for row in data:
        # Asumiendo que la fecha está en el formato 'YYYY-MM-DD HH:MM:SS'
        fecha = row[1]  # La fecha está en la segunda columna
        nivel_tanque = row[2]  # El nivel está en la tercera columna
        porcentaje = row[3]  # El porcentaje está en la cuarta columna

        # Generar el estado en función del porcentaje
        if porcentaje >= 90:
            estado = "Nivel óptimo"
        elif porcentaje >= 70:
            estado = "Nivel bajo"
        else:
            estado = "¡ALERTA! Tanque casi vacío"

        # Insertar la fila en la tabla
        table.insert("", "end", values=(fecha, nivel_tanque, porcentaje, estado))

    table.pack(fill=tk.BOTH, expand=True)

    # Mostrar estadísticas
    avg_tank = sum(row[2] for row in data) / len(data) if data else 0
    avg_humidity = sum(row[3] for row in data) / len(data) if data else 0
    alert_days = sum(1 for row in data if "¡ALERTA!" in ("Nivel bajo" if row[3] < 70 else "Nivel óptimo"))

    stats_label = tk.Label(main_frame, text=f"Estadísticas:\n"
                                            f"Promedio del nivel del tanque: {avg_tank:.2f} cm\n"
                                            f"Promedio de humedad: {avg_humidity:.2f}%\n"
                                            f"Días con alertas: {alert_days}",
                           font=("Arial", 12), justify=tk.LEFT)
    stats_label.pack(pady=10)

    back_button = ttk.Button(main_frame, text="Volver", command=show_main_screen)
    back_button.pack(pady=10)




# Configuración inicial de la ventana
root = tk.Tk()
root.title("Monitoreo de Tanques")
root.geometry("500x500")

# Variables para los datos de la interfaz
tank_level = tk.StringVar(value="---")
humidity_level = tk.StringVar(value="---")
leak_sensor = tk.StringVar(value="---")

# Frame principal
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Mostrar la pantalla principal
show_main_screen()

# Iniciar el hilo de lectura del Arduino
arduino_thread = threading.Thread(target=read_arduino_data, daemon=True)
arduino_thread.start()

# Ejecutar el loop principal de Tkinter
root.mainloop()
