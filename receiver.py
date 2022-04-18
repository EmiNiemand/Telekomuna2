from numpy import char
import portInitialize as por
import serial as ser
import variables as var
import checksums as che


def main():
    port_name = "COM2"
    serial_port = por.startSerialPort(port_name)
    data = receive(serial_port, var.NAK)
    data = bytes(removeGarbage(data))
    print(data.decode("utf-8"))
    serial_port.close()


def removeGarbage(data: bytes):
    data = bytearray(data)
    while data[-1] == 26:
        del data[-1]
    return data


def receive(serial_port: ser.Serial, check_sum_type: char):
    result = bytearray()
    for i in range(20):
        serial_port.write(check_sum_type)
        packet_number = 1
        while True:
            try:
                data_block = checkPacket(serial_port, packet_number, check_sum_type)
                result += bytearray(data_block)
                serial_port.write(var.ACK)
                packet_number += 1
            except NAKException:
                serial_port.read(serial_port.in_waiting)
                serial_port.write(var.NAK)
            except ACKException:
                serial_port.write(var.ACK)
                return bytes(result)
            except NoAcceptFromSenderException:
                break

    raise NoAcceptFromSenderException


def checkPacket(serial_port: ser.Serial, packet_number: int, check_sum_type: char):
    checkHeader(serial_port, packet_number)
    data_block = serial_port.read(128)
    if check_sum_type == var.NAK:
        message_sum = serial_port.read(1)
    else:
        message_sum = serial_port.read(2)
    calculated_sum = che.calculateChecksum(data_block, check_sum_type)

    if message_sum != calculated_sum:
        raise InvalidChecksumException

    return data_block


def checkHeader(serial_port: ser.Serial, packet_number: int):
    header = serial_port.read(1)

    if len(header) == 0:
        raise NoAcceptFromSenderException
    elif header == var.EOT:
        raise ACKException
    elif header != var.SOH:
        raise InvalidHeaderException

    message_number = serial_port.read(1)
    message_number_integer = int.from_bytes(message_number, "big")

    if packet_number % 255 != message_number_integer:
        raise WrongPacketNumberException

    message_number_completion = serial_port.read(1)
    message_number_completion_integer = int.from_bytes(message_number_completion, "big")

    if 255 - (packet_number % 255) != message_number_completion_integer:
        raise WrongPacketNumberException

    return bytearray(header) + bytearray(message_number) + bytearray(message_number_completion)


class NAKException:
    pass


class ACKException:
    pass


class NoAcceptFromSenderException:
    pass


class InvalidChecksumException:
    pass


class InvalidHeaderException:
    pass


class WrongPacketNumberException:
    pass


if __name__ == '__main__':
    main()

