import tkinter as tk
from tkinter import ttk
import serial
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from bd import save_to_db

# Configuración del puerto serial para Arduino
arduino_port = 'COM4'  # Cambia esto según tu sistema
arduino = serial.Serial(port=arduino_port, baudrate=9600, timeout=1)

# Variables para almacenar los datos históricos
timestamps = []
water_levels = []

# Variables para almacenar los datos temporales
temp_timestamp = None
temp_water_level = None
temp_tank_percentage = None
temp_tank_status = None

# Intervalo en segundos para guardar los datos (Ej. cada 60 segundos)
SAVE_INTERVAL = 60
last_save_time = time.time()

# Función para actualizar los datos del tanque y sensor de lluvia
def update_tank_display(tank_percentage, water_level, tank_status):
    # Actualizar los valores de los widgets
    tank_level.set(f"{water_level} cm")
    humidity_level.set(f"{tank_percentage}%")
    leak_sensor.set(f"Estado del Tanque: {tank_status}")

    # Dibuja el nivel de agua
    canvas.delete("water")  # Borra el agua anterior
    water_height = (tank_percentage / 100) * 200
    canvas.create_rectangle(50, 200 - water_height, 150, 200, fill="deepskyblue", tags="water")
    
    # Cambiar el color del contorno según el nivel del tanque
    if tank_percentage >= 70:
        canvas.itemconfig(tank_outline, outline="red", width=3)
    elif tank_percentage >= 30:
        canvas.itemconfig(tank_outline, outline="green", width=3)
    else:
        canvas.itemconfig(tank_outline, outline="yellow", width=3)

    # Agregar los nuevos datos a la lista de gráficos
    timestamps.append(time.strftime("%H:%M:%S"))
    water_levels.append(water_level)

    # Limitar los datos para mostrar solo los últimos 10 minutos
    if len(timestamps) > 10:
        timestamps.pop(0)
        water_levels.pop(0)

    # Actualizar el gráfico
    update_graph()


# Función para actualizar la gráfica
import numpy as np

def update_graph():
    ax.clear()  # Limpiar el gráfico anterior
    ax.plot(timestamps, water_levels, marker='o', color='deepskyblue', linestyle='-', linewidth=2)

    # Configurar los ejes
    ax.set_xlabel("Tiempo (HH:MM:SS)", fontsize=10)
    ax.set_ylabel("Nivel del Tanque (cm)", fontsize=10)
    ax.set_title("Comportamiento del Nivel de Agua en el Tanque", fontsize=12)

    # Ajustar los ticks del eje Y para que sean cada 1 cm
    y_min, y_max = ax.get_ylim()  # Obtener los límites actuales del eje Y
    y_ticks = np.arange(np.floor(y_min), np.ceil(y_max)+1, 1)  # Crear los ticks con intervalos de 1 cm
    ax.set_yticks(y_ticks)

    # Redibujar el gráfico
    canvas_graph.draw()


# Función para actualizar los datos y la gráfica cada minuto
def refresh_data_and_graph(root):
    # Aquí va la lógica para leer los nuevos datos del Arduino
    # ...

    # Llamamos a la función que actualiza la gráfica
    update_graph()

    # Reprogramar la actualización después de un minuto
    root.after(60000, refresh_data_and_graph, root)

# Función que lee datos del puerto serial (de Arduino)
def read_arduino_data():
    global temp_timestamp, temp_water_level, temp_tank_percentage, temp_tank_status, temp_rain_humidity, last_save_time
    while True:
        try:
            if arduino.in_waiting > 0:
                line = arduino.readline().decode('utf-8').strip()  # Leer línea desde el Arduino
                if line:
                    # Si la línea contiene los datos del tanque
                    if "Nivel de agua:" in line:
                        parts = line.split(" ")
                        water_level = float(parts[3])  # Nivel en cm
                        tank_percentage = float(parts[5][1:-2])  # Porcentaje
                        tank_status = " ".join(parts[7:])  # El estado del tanque

                        # Obtener la fecha y hora actual
                        fecha_hora = time.strftime("%Y-%m-%d %H:%M:%S")

                        # Guardar los datos temporalmente
                        temp_timestamp = fecha_hora
                        temp_water_level = water_level
                        temp_tank_percentage = tank_percentage
                        temp_tank_status = tank_status

                        # Actualiza la interfaz gráfica con los nuevos datos
                        update_tank_display(tank_percentage, water_level, tank_status)

                    # Si la línea contiene los datos del sensor de lluvia
                    elif "Humedad: " in line:
                        # Extraer la humedad del sensor de lluvia
                        rain_humidity = int(line.split(": ")[1])  # Obtener el valor después de "Humedad: "
                        temp_rain_humidity = rain_humidity  # Guardar la humedad del sensor de lluvia

                        # Mostrar el valor en la interfaz gráfica (si lo deseas)
                        fuga_sensor.set(f"Humedad Sensor de Lluvia: {rain_humidity}%")

                        if rain_humidity >= 900:
                            fuga_sensor.set("No hay fugas")
                        elif rain_humidity >= 700:
                            fuga_sensor.set("Humedad baja, posible fuga pequena")
                        elif rain_humidity >= 500:
                            fuga_sensor.set("Humedad media, posible fuga")
                        elif rain_humidity >= 300:
                            fuga_sensor.set("Humedad alta, posible fuga detectada")
                        else:
                            fuga_sensor.set("Fuga detectada o psoible lluvia")

                    # Verificar si ha pasado el intervalo de tiempo para guardar los datos
                    if time.time() - last_save_time >= SAVE_INTERVAL:
                        # Guardar en la base de datos
                        save_to_db(temp_timestamp, temp_water_level, temp_tank_percentage, temp_rain_humidity)

                        # Actualizar el tiempo de la última vez que se guardaron los datos
                        last_save_time = time.time()

        except Exception as e:
            print(f"Error leyendo datos del Arduino: {e}")


# Función para mostrar la pantalla principal
def show_main_screen():
    for widget in main_frame.winfo_children():
        widget.pack_forget()

    # Frame para la información del tanque
    info_frame = tk.Frame(main_frame, bg="#e0f7fa", width=300)
    info_frame.pack(side="left", fill="y", padx=20)

    tk.Label(info_frame, text="Nivel del Tanque:", font=("Segoe UI", 14), bg="blue", fg="white").pack(pady=8)
    tk.Label(info_frame, textvariable=tank_level, font=("Segoe UI", 12), bg="#e0f7fa", fg="black").pack(pady=5)
    tk.Label(info_frame, text="Porcentaje de Llenado:", font=("Segoe UI", 14), bg="blue", fg="white").pack(pady=8)
    tk.Label(info_frame, textvariable=humidity_level, font=("Segoe UI", 12), bg="#e0f7fa", fg="black").pack(pady=5)
    tk.Label(info_frame, text="Estado del Tanque:", font=("Segoe UI", 14), bg="blue", fg="white").pack(pady=8)
    tk.Label(info_frame, textvariable=leak_sensor, font=("Segoe UI", 12), bg="#e0f7fa", fg="black").pack(pady=5)
    tk.Label(info_frame, text="Fugas del Tanque:", font=("Segoe UI", 14), bg="blue", fg="white").pack(pady=8)
    tk.Label(info_frame, textvariable=fuga_sensor, font=("Segoe UI", 12), bg="#e0f7fa", fg="black").pack(pady=5)


    

    # Canvas para mostrar el gráfico del tanque
    global canvas
    canvas = tk.Canvas(info_frame, width=200, height=250, bg="white", bd=2, relief="solid")
    canvas.pack(pady=20)

    global tank_outline
    tank_outline = canvas.create_rectangle(50, 0, 150, 200, outline="black", width=2)

    # Botón para ver tabla y estadísticas
    ttk.Button(info_frame, text="Ver Tabla y Estadísticas", command=show_table, style="TButton").pack(pady=15)

    # Pantalla principal con el gráfico
    global ax, canvas_graph
    fig, ax = plt.subplots(figsize=(5, 4))  # Crear figura y ejes para la gráfica
    ax.set_xlabel("Tiempo (HH:MM:SS)", fontsize=10)
    ax.set_ylabel("Nivel del Tanque (cm)", fontsize=10)
    ax.set_title("Comportamiento del Nivel de Agua en el Tanque", fontsize=12)

    # Insertar el gráfico en la ventana de Tkinter
    canvas_graph = FigureCanvasTkAgg(fig, master=main_frame)
    canvas_graph.get_tk_widget().pack(side="right", padx=20)
    canvas_graph.draw()

# Función para mostrar la tabla de datos históricos
def show_table():
    for widget in main_frame.winfo_children():
        widget.pack_forget()

    # Crear tabla
    table = ttk.Treeview(main_frame, columns=("Fecha", "Nivel del Tanque", "Humedad", "Estado"), show="headings")
    table.heading("Fecha", text="Fecha")
    table.heading("Nivel del Tanque", text="Nivel del Tanque (cm)")
    table.heading("Humedad", text="Porcentaje (%)")
    table.heading("Estado", text="Estado")

    from bd import get_all_readings  # Asegúrate de importar la función
    data = get_all_readings()  # Llama a la función que obtiene las lecturas

    for row in data:
        fecha = row[1]
        nivel_tanque = row[2]
        porcentaje = row[3]

        if porcentaje >= 70:
            estado = "Tanque casi lleno"
        elif porcentaje >= 30:
            estado = "Nivel óptimo"
        elif porcentaje >= 15:
            estado = "¡ALERTA! Tanque en nive bajo"
        else:
            estado = "¡ALERTA! Tanque casi vacío"

        table.insert("", "end", values=(fecha, nivel_tanque, porcentaje, estado))

    table.pack(fill=tk.BOTH, expand=True)

    # Mostrar estadísticas
    avg_tank = sum(row[2] for row in data) / len(data) if data else 0
    avg_humidity = sum(row[3] for row in data) / len(data) if data else 0
    #alert_days = len([row for row in data if row[3] < 30])

    stats_frame = tk.Frame(main_frame, bg="#e0f7fa", padx=20)
    stats_frame.pack(fill="x")
    tk.Label(stats_frame, text=f"Promedio Nivel de Tanque: {avg_tank:.2f} cm", font=("Segoe UI", 12), bg="#e0f7fa").pack(pady=10)
    tk.Label(stats_frame, text=f"Promedio Porcentaje de Llenado: {avg_humidity:.2f}%", font=("Segoe UI", 12), bg="#e0f7fa").pack(pady=10)
    #tk.Label(stats_frame, text=f"Días con ALERTA (Nivel bajo): {alert_days}", font=("Segoe UI", 12), bg="#e0f7fa").pack(pady=10)

    # Botón de regreso
    ttk.Button(main_frame, text="Regresar a la Pantalla Principal", command=show_main_screen).pack(pady=10)

# Función principal para inicializar la interfaz
def main():
    root = tk.Tk()
    root.title("Monitoreo de Tanque en Zonas Remotas")
    root.geometry("1000x600")
    root.config(bg="#e0f7fa")

    global main_frame
    main_frame = tk.Frame(root, bg="#e0f7fa")
    main_frame.pack(fill="both", expand=True)

    global tank_level, humidity_level, leak_sensor, fuga_sensor
    tank_level = tk.StringVar()
    humidity_level = tk.StringVar()
    leak_sensor = tk.StringVar()
    fuga_sensor = tk.StringVar()

    # Llamar a la pantalla principal
    show_main_screen()

    refresh_data_and_graph(root)  # Iniciar la actualización de los datos y la gráfica

    # Iniciar la lectura del Arduino en un hilo separado
    threading.Thread(target=read_arduino_data, daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    main()
