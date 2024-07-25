import time
import serial
import serial.tools.list_ports


def connection_test():
    target_name = "2303"
    ser_name = ""
    
    ports = serial.tools.list_ports.comports()
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


def initialize_keithley2000(serial_connection):
    # Initialize Keithley 2000 settings
    serial_connection.write(b":SYST:BEEP:STAT OFF\n")
    serial_connection.write(b'*RST\n')  # Reset the instrument
    serial_connection.write(b":SYST:BEEP:STAT OFF\n")
    time.sleep(1)  # Wait for reset to complete
    serial_connection.write(b':CONF:VOLT:DC\n')  # Configure for DC voltage measurement
    serial_connection.write(b':SENS:VOLT:DC:NPLC 1\n')  # Set integration time to 10 power line cycles
    serial_connection.write(b':SENS:VOLT:DC:RANG 10\n')  # Enable auto range


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