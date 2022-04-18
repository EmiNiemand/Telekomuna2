import serial as ser


def startSerialPort(port: str, baudrate: int = 9600, timeout=3):
    serial_port = ser.Serial()
    serial_port.baudrate = baudrate
    serial_port.port = port
    serial_port.timeout = timeout
    serial_port.parity = ser.PARITY_NONE
    serial_port.stopbits = ser.STOPBITS_ONE
    serial_port.bytesize = ser.EIGHTBITS
    serial_port.open()
    return serial_port


