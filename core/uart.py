import serial

def init_uart():
    return serial.Serial("/dev/ttyS0", 9600)

def write_string(msg, ser):
    ser.write(bytes(msg, 'utf-8'))


