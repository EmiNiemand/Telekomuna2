from numpy import char
import portInitialize as por
import serial as ser
import variables as var
import checksums as che


def main():
    test = "Duuuuuuuuuuuuuuuzo tekstu. Tak duzo, ze az duuuuuuuuuuzo miejsca zajmie i to dobrze, bo taka jest rola" \
           " tego tekstu, bo po co mi tekst ktory jest maly? Malego niewarto wysylac, a duzy to juz tak, czemu nie?" \
           " Fajnie byc tak skryba... Jak sie straci prace to mozna potem sadzic marchew dzieki zdobytemu " \
           "doswiadczeniu. "

    port_number = "COM1"
    serial_port = por.startSerialPort(port_number)
    send(serial_port, bytes(test, 'ascii'))
    serial_port.close()


def send(serial_port: ser.Serial, data: bytes):
    check_sum_type = waitForChecksum(serial_port)
    packets = preparePackets(data, check_sum_type)

    packet_number = 0
    while packet_number < len(packets):
        serial_port.write(packets[packet_number])

        response = serial_port.read(1)
        if response == var.ACK:
            packet_number += 1
        elif response == var.NAK:
            continue
        else:
            print("Błąd! Dostałem złą odpowiedź :(")

    serial_port.write(var.EOT)
    response = serial_port.read()
    while response != var.ACK:
        serial_port.write(var.EOT)
        response = serial_port.read()


def waitForChecksum(serial_port: ser.Serial):
    for i in range(6):
        message = serial_port.read(1)
        if message == var.NAK:
            return var.NAK
        elif message == var.C:
            return var.C

    print("Błąd! Nikt nie chce mojej wiadomości :(")


def preparePackets(data: bytes, check_sum_type: char):
    # dzielenie wiadomości na bloki po 128 bitów
    blocks = [data[i:i + 128] for i in range(0, len(data), 128)]

    packets = []
    # rób tyle razy ile jest bloków
    for packet_number in range(len(blocks)):
        packet = bytearray()
        packet += createHeader(packet_number)

        # dopełnienie ostatniego bloku do 128 bitów i dodanie bloków do pakietu
        if len(blocks[packet_number]) < 128:
            blocks[packet_number] = fillBlockWithSUB(blocks[packet_number])
        packet += bytearray(blocks[packet_number])

        # liczenie check sumy i dodanie do pakietu
        calculated_check_sum = che.calculateChecksum(blocks[packet_number], check_sum_type)
        packet += bytearray(calculated_check_sum)
        packets.append(bytes(packet))

    return packets


def createHeader(packet_number: int):
    header = bytearray(var.SOH)
    packet_number += 1
    header.append(packet_number % 255)
    header.append(255 - (packet_number % 255))
    return header


def fillBlockWithSUB(block: bytes):
    block = bytearray(block)
    for i in range(128 - len(block)):
        block += bytearray(var.SUB)
    return bytes(block)


if __name__ == '__main__':
    main()
