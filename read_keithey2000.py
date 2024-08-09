import os
import sys
import time
import serial
from serial.tools import list_ports


def connection_test():
    target_name = "2303"
    ser_name = ""
    
    ports = list_ports.comports()
    for port in ports:
        # print(port.hwid)
        if target_name in port.hwid:
            ser_name = port.device

    if ser_name == "": exit("ERROR: DC meter does not find.")
    
    # ser = serial.Serial(ser_name, write_timeout=3, timeout=5)
    # # ser.write("*IDN?\n".encode())
    # # # ser.write(":SYST:BEEP:STAT OFF\r\n".encode())
    # # back = ser.readline().decode().strip()
    # # ser.write(b":SYST:BEEP:STAT OFF\n")
    # # print(back)
    # ser.close()
    
def setup():
    Parameter = {}

    try:
        ports = list(list_ports.comports())
        port_number = int(sys.argv[2])
    except IndexError:
        if (len(ports) == 0):
            print("デバイスが認識できません\r\n接続を確認してください")
            exit()
        i = 0
        for p in ports:
            i += 1
            print("[" + str(i) + "]." + p.description)
    
        port_number  = input("Keithley2000 接続ポートの[]番号：")
        # port_number = 1
        while True:
            try:
                port_number = int(port_number)
                if port_number > len(ports):
                    raise ValueError
                if port_number == 0:
                    raise ValueError
            except ValueError:
                print("エラー：無効な入力")
                port_number  = input("Keithley2000 接続ポートの[]番号：")
            else:
                break

    try:
        ser = []
        port_name = ports[port_number-1].device
        ser = serial.Serial(port_name , 9600, timeout=2, write_timeout=5)
        print(">>> " + port_name, end="    ")
        print("Checking Connection")
        ser.write("*IDN?\r\n".encode())

        print("AAAA")
        
        back = ser.readline().decode()
        # back = "a"
        if not back.startswith(""):
            Parameter.update({"MultimeterStatus":True})
            print(back.replace("\r\n",''), end="    ")
            print("Connection OK")
        else:
            raise serial.SerialException
    except serial.SerialException:
        Parameter.update({"MultimeterStatus":False})
        print("ERROR : Could't Connect to Multimeter")
        
        #exit()

    Parameter.update({"MultimeterPortName":port_name})

    return Parameter


def initialize_keithley2000(serial_connection):
    # Initialize Keithley 2000 settings
    serial_connection.write(b":SYST:BEEP:STAT OFF\n")
    serial_connection.write(b'*RST\n')  # Reset the instrument
    serial_connection.write(b":SYST:BEEP:STAT OFF\n")
    time.sleep(1)  # Wait for reset to complete
    serial_connection.write(b':CONF:VOLT:DC\n')  # Configure for DC voltage measurement
    serial_connection.write(b':SENS:VOLT:DC:NPLC 1\n')  # Set integration time to 10 power line cycles
    serial_connection.write(b':SENS:VOLT:DC:RANG 10\n')


def read_keithley2000(serial_connection):
    # Trigger a single voltage measurement
    serial_connection.write(b':READ?\n')
    time.sleep(1)  # Wait for measurement to complete
    voltage = serial_connection.readline().decode().strip()
    try:
        voltage = float(voltage)
    except TypeError:
        print(f"ERROR: TypeError {voltage}")
        voltage = 9.99999
    
    #キャリブレーション用MagicNumber 測定値を見ながら調整した 
    microTesla = round(voltage*1000 - (-0.0098*pow(voltage,5)+0.0087*pow(voltage,4)+0.0861*pow(voltage,3)-0.0861*pow(voltage,2)-0.1652*pow(voltage,1)-0.11*pow(voltage,1)+0.25), 3)
    if abs(microTesla) > 2000.: microTesla = 9999.99
    
    return microTesla

def main():
    # Replace with your RS232 port and baud rate
    port = 'COM3'
    baudrate = 9600

    # Initialize serial connection
    with serial.Serial(port, baudrate, timeout=1, write_timeout=3) as ser:
        initialize_keithley2000(ser)
        time.sleep(2)  # Allow some time for the instrument to settle

        while True:
            microTesla = read_keithley2000(ser)
            print(f"Measured Magnetic Field: {microTesla} μT")
            time.sleep(0.2)  # Measure every 1 second

    # return [result, 0, cnn_digit, 0, 0]

if __name__ == "__main__":
    
    connection_test()
    # read_keithley2000()
    # ser = serial.Serial("COM3")
    
    # initialize_keithley2000(ser)
    
    # volt = read_keithley2000(ser)
    
    # print(volt)
    
    main()
    
    # ser.close()