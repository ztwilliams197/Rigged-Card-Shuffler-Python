from uart import *
from time import sleep

if __name__ == '__main__':
    ser = init_uart()
    print("UART Init'd")   

    num = 0
    while True:    
        if(ser.in_waiting > 0):
            received = ser.read(ser.in_waiting)
            print(received.decode('utf-8'))
        
        sleep(1)
        '''      
        print("a")
        ser.write(bytes("A", 'utf-8'))
        ser.flush()
        print("b")
        '''

        print(f"Sending: {num}")
        ser.write(num.to_bytes(1, 'little'))
        print(num.to_bytes(1, 'little'))
        num = (num + 1) % 256
