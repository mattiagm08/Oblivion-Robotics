import serial

ser = serial.Serial(port='dev/ttyUSB0', baudrate= 9600)

while True:
    line = ser.readline().decode('utf-8')
    print(line)

    