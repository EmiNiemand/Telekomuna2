import port_initialize as pi
import Exceptions as exc
import serial as ser
import variables as var
import checksums as cs

def main():

    test = "przykladowa wiadomosc do testu i pisze byle blablabla zeby zapelnic kilkset bajtow bo moge czemu nie kto" \
    " mi zabroni chyba raczej nikt bo czemu ktos mialby. Jestem wolnym czlowiekiem robie co chce wiec ezz a wy co" \
    " dalej niewolnicy systemu podatkowego??? Pewnie tak, a ja nie place bo mnie nie stac."

    port_name = "COM1"
    serial_port = pi.initialize_serial_port(port_name)
    send(serial_port, bytes(test, 'ascii'))
    serial_port.close()


#===========================================Send=========================================
def send(serial_port: ser.Serial, data: bytes):
    check_sum_type = dont_send_until_checksum_got(serial_port)
    packets = prepare_packets(data, check_sum_type)

    packet_number = 0
    while packet_number < len(packets):
        serial_port.write(packets[packet_number])

        # when receiver sends NAK send packet another time
        response = serial_port.read(1)
        if response == var.ACK:
            packet_number += 1
        elif response == var.NAK:
            continue
        else:
            raise exc.UnexpectedResponseException

    response = None
    while response != var.ACK:
        serial_port.write(var.EOT)
        response = serial_port.read()



def dont_send_until_checksum_got(serial_port: ser.Serial):
    for i in range(6):
        message = serial_port.read(1)
        if message == var.NAK:
            return pi.ChecksumEnum.algebraic
        elif message == var.C:
            return pi.ChecksumEnum.crc

    raise exc.TransferNotStartedException


def prepare_packets(data: bytes, check_sum_type: pi.ChecksumEnum):
    # split data intro 128 bytes long blocks
    blocks = [data[i:i + 128] for i in range(0, len(data), 128)]

    packets = []
    for packet_number in range(len(blocks)):
        packet = bytearray()
        packet += create_header(packet_number)

        # fill last packet with ^z to make it 128 byte length
        if len(blocks[packet_number]) < 128:
            blocks[packet_number] = fill_block_with_sub(blocks[packet_number])

        # append data block
        packet += bytearray(blocks[packet_number])

        # calculate check sum and append it to packet
        calculated_check_sum = cs.calculate_checksum(blocks[packet_number], check_sum_type)
        packet += bytearray(calculated_check_sum)

        # append packet to packet list
        packets.append(bytes(packet))

    return packets


def create_header(packet_number: int):
    # append checkSumType
    header = bytearray(var.SOH)

    # packet number starts at 1 when is lower than 255
    packet_number += 1

    # append packet number and it's compliment
    header.append(packet_number % 255)
    header.append(255 - (packet_number % 255))

    return header


def fill_block_with_sub(block: bytes):
    block = bytearray(block)
    for i in range(128 - len(block)):
        block += bytearray(var.SUB)
    return bytes(block)



if __name__ == '__main__':
    main()

