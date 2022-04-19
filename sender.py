from numpy import char
import serial as ser
import variables as var
import checksums as che


def sendMessage(serial_port: ser.Serial, data: bytes):
    # Sprawdzam rodzaj checksumy (CRC / algebraiczna)
    check_sum_type = waitForChecksum(serial_port)
    # Przygotowuje pakiety w zależności od rodzaju checksumy
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
            print("Błąd! Wysłana została nieodpowiednia wiadomość zwrotna")
            raise Exception

    serial_port.write(var.EOT)
    response = serial_port.read()
    while response != var.ACK:
        serial_port.write(var.EOT)
        response = serial_port.read()


def waitForChecksum(serial_port: ser.Serial):
    # Odczytuję bajt z portu i sprawdzam czy znak to NAK czy C
    # (jak NAK to checksuma algebraiczna, jak C to CRC)
    for i in range(6):
        message = serial_port.read(1)
        if message == var.NAK:
            return var.NAK
        elif message == var.C:
            return var.C
    print("Błąd! Nikt nie chce mojej wiadomości :(")
    raise Exception


def preparePackets(data: bytes, check_sum_type: char):
    # dzielenie wiadomości na bloki po 128 bajtów
    blocks = [data[i:i + 128] for i in range(0, len(data), 128)]

    packets = []
    # rób tyle razy ile jest bloków
    for packet_number in range(len(blocks)):
        packet = bytearray()
        # Tworzenie 3-bajtowego headera:
        # - bajt znaku SOH,
        # - bajt numeru bloku,
        # - bajt dopełnienia tego bloku do 255 (255 - numer bloku).
        header = bytearray(var.SOH)
        header.append((packet_number + 1) % 255)
        header.append(255 - (packet_number % 255))
        packet += header

        # dopełnienie ostatniego bloku do 128 bajtów (znakami SUB) i dodanie ich do pakietu
        if len(blocks[packet_number]) < 128:
            blocks[packet_number] = fillBlockWithSUB(blocks[packet_number])
        packet += bytearray(blocks[packet_number])

        # liczenie check sumy i dodanie do pakietu
        calculated_check_sum = che.calculateChecksum(blocks[packet_number], check_sum_type)
        packet += bytearray(calculated_check_sum)
        packets.append(bytes(packet))

    return packets


# Dodawanie na koniec bloku znaków SUB do osiągnięcia 128 bajtów.
def fillBlockWithSUB(block: bytes):
    block = bytearray(block)
    for i in range(128 - len(block)):
        block += bytearray(var.SUB)
    return bytes(block)



