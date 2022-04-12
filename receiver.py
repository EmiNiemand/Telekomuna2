import port_initialize as pi
import Exceptions as exc
import serial as ser
import variables as var
import checksums as cs


def clear_data(data: bytes):
    data = bytearray(data)
    while data[-1] == 26:
        del data[-1]
    return data


#========================Main========================
def main():

    port_name = "COM2"
    serial_port = pi.initialize_serial_port(port_name)
    data = receive(serial_port, pi.ChecksumEnum.algebraic)
    data = bytes(clear_data(data))
    print(data.decode("utf-8"))
    serial_port.close()


#=======================Receive===========================
def receive(serial_port: ser.Serial, check_sum_type: pi.ChecksumEnum):
    result = bytearray()
    # Wait for sender response
    for i in range(20):
        serial_port.write(check_sum_type.value)
        packet_number = 1
        while True:
            try:
                data_block = read_and_check_packet(serial_port, packet_number, check_sum_type)
                result += bytearray(data_block)
                serial_port.write(var.ACK)
                packet_number += 1
            except exc.NAKException:
                serial_port.read(serial_port.in_waiting)
                serial_port.write(var.NAK)
            except exc.EOTHeaderException:
                serial_port.write(var.ACK)
                return bytes(result)
            except exc.SenderNotAcceptedTransferException:
                break

    raise exc.SenderNotAcceptedTransferException


def read_and_check_packet(serial_port: ser.Serial, packet_number: int, check_sum_type: pi.ChecksumEnum):
    header = check_header(serial_port, packet_number)
    # Calculate check sum and extract data data_block
    data_block = serial_port.read(128)
    message_sum = read_checksum(serial_port, check_sum_type)
    calculated_sum = cs.calculate_checksum(data_block, check_sum_type)

    # Check is transmitted checksum is the same as calculated
    if message_sum != calculated_sum:
        raise exc.InvalidChecksumException

    return data_block


def check_header(serial_port: ser.Serial, packet_number):
    # Check is header good
    header = serial_port.read(1)

    if len(header) == 0:
        raise exc.SenderNotAcceptedTransferException
    elif header == var.EOT:
        raise exc.EOTHeaderException
    elif header != var.SOH:
        raise exc.InvalidHeaderException

    message_number = serial_port.read(1)
    message_number_integer = int.from_bytes(message_number, "big")

    if packet_number % 255 != message_number_integer:
        raise exc.WrongPacketNumberException

    message_number_completion = serial_port.read(1)
    message_number_completion_integer = int.from_bytes(message_number_completion, "big")

    if 255 - (packet_number % 255) != message_number_completion_integer:
        raise exc.WrongPacketNumberException

    return bytearray(header) + bytearray(message_number) + bytearray(message_number_completion)


def read_checksum(serial_port: ser.Serial, check_sum_type: pi.ChecksumEnum):
    if check_sum_type == pi.ChecksumEnum.algebraic:
        return serial_port.read(1)
    else:
        return serial_port.read(2)


if __name__ == '__main__':
    main()

