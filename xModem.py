from enum import Enum
import serial as s
import variables as v
import checksums as cs

class WhichCheckSum(Enum):
    algebraic = v.SOH
    crc = v.C

class TransferNotStartedByReceiverException(Exception):
    pass

class UnexpectedRespondException(Exception):
    pass


def initialize_serial_port(string):
    serial_port = s.Serial()
    serial_port.baudrate = 9600
    serial_port.port = string
    serial_port.timeout = 3
    serial_port.parity = s.PARITY_NONE
    serial_port.stopbits = s.STOPBITS_ONE
    serial_port.bytesize = s.EIGHTBITS
    serial_port.open()
    return serial_port


def send_message(serial_port: s.Serial, data):
    check_sum_type = check_checksum_start_sending(serial_port)
    packets = prepare_packets(data, check_sum_type)

    packet_number = 0
    while packet_number < len(packets):
        serial_port.write(packets[packet_number])

        # when receiver sends NAK send packer another time
        response = serial_port.read(1)
        if response == v.ACK:
            packet_number += 1
        elif response == v.NAK:
            continue
        else:
            raise UnexpectedRespondException

    response = None
    while response != v.ACK:
        serial_port.write(v.EOT)
        response = serial_port.read()


def check_checksum_start_sending(serial_port: s.Serial):
    for i in range(6):
        message = serial_port.read(1)
        if message == v.NAK:
            return WhichCheckSum.algebraic
        elif message == v.C:
            return WhichCheckSum.crc

    raise TransferNotStartedByReceiverException


def create_header(check_sum_type, packet_number):
    # append checkSumType
    header = bytearray(check_sum_type.value)

    # packet number starts at 1 when is lower than 255
    packet_number += 1

    # append packet number and it's compliment
    header.append(packet_number % 255)
    header.append(255 - (packet_number % 255))

    return header


def fill_block_with_subs(block):
    block = bytearray(block)
    for i in range(128 - len(block)):
        block += bytearray(v.SUB)

    return bytes(block)


def prepare_packets(data, check_sum_type):
    # split data into 128 bytes long blocks
    blocks = [data[i:i + 128] for i in range(0, len(data), 128)]

    packets = []
    for packet_number in range(len(blocks)):
        packet = bytearray()
        packet += create_header(check_sum_type, packet_number)

        # fill last packet with subs to make it 128 byte length
        if len(blocks[packet_number]) < 128:
            blocks[packet_number] = fill_block_with_subs(blocks[packet_number])

        # append data block
        packet += bytearray(blocks[packet_number])

        # calculate checksum and append it to packet
        calculated_check_sum = None
        if check_sum_type == WhichCheckSum.algebraic:
            calculated_check_sum = cs.algebraic_checksum(blocks[packet_number])
        elif check_sum_type == WhichCheckSum.crc:
            calculated_check_sum = cs.crc_checksum(blocks[packet_number])

        packet += bytearray(calculated_check_sum)

        # append packet to packet list
        packets.append(bytes(packet))

    return packets

