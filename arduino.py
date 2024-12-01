# arduino.py
import serial
import time

# Configura el puerto serial (ajusta 'COMX' o '/dev/ttyUSBX' según tu sistema)
arduino = serial.Serial(port='COM4', baudrate=9600, timeout=1)  # Cambia 'COM4' por el puerto correcto

def read_arduino_data():
    try:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()  # Leer y decodificar
            return line
    except Exception as e:
        print(f"Error leyendo datos del Arduino: {e}")
    return None

while True:
    data = read_arduino_data()
    if data:
        print(f"Datos recibidos: {data}")  # Puede ser algo como "70,45,No" (nivel, humedad, fuga)
    time.sleep(1)
