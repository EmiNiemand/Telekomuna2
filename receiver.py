from numpy import char
import serial as ser
import variables as var
import checksums as che


# ===========================Functions==================
def receiveMessage(serial_port: ser.Serial, check_sum_type: char):
    message = bytearray()
    for i in range(20):
        # Wysyłanie jakiego rodzaju pakiety chcę otrzymywać.
        serial_port.write(check_sum_type)
        packet_number = 1
        while True:
            # Sprawdzanie poprawności pakietu
            block_of_data, state = checkPacket(serial_port, packet_number, check_sum_type)

            # Jeśli wszystko dobrze:
            match state:
                case 0:
                    # Zapisuje kolejne części wiadomości do rozwiązania.
                    message += bytearray(block_of_data)
                    # Zwraca znak ACK do nadawcy.
                    serial_port.write(var.ACK)
                    packet_number += 1
                case 1:
                    # Czyszczenie portu.
                    # Jeśli nie odczytany pakiet nie jest prawidłowy, to wyślij NAK,
                    # żeby pakiet został wysłany jeszcze raz.
                    serial_port.read(serial_port.in_waiting)
                    serial_port.write(var.NAK)
                case 2:
                    # Zakończenie transferu i zwrócenie wiadomości.
                    serial_port.write(var.ACK)
                    return bytes(message)
                case 3:
                    # Jeżeli transfer nie został zaakceptowany.
                    break

    print("Transfer nie został zaakceptowany lub skończył się czas nasłuchiwania.")
    raise Exception


def checkPacket(serial_port: ser.Serial, packet_number: int, check_sum_type: char):
    # sprawdzanie poprawności nagłówka.
    header = checkHeader(serial_port, packet_number)
    if header != 0:
        return bytearray(), header

    # Odczytanie bajtów wiadomości.
    data_block = serial_port.read(128)

    # Odczytanie checksumy.
    if check_sum_type == var.NAK:
        message_checksum = serial_port.read(1)
    elif check_sum_type == var.C:
        message_checksum = serial_port.read(2)

    # Sprawdzanie, czy odczytana checksuma jest równa obliczonej na podstawie bloku wiadomości.
    calculated_checksum = che.calculateChecksum(data_block, check_sum_type)

    if message_checksum != calculated_checksum:
        return bytearray(), 1

    return data_block, 0


def checkHeader(serial_port: ser.Serial, packet_number: int):
    # Sprawdzanie, czy pierwszy bajt jest równy znakowi SOH.
    header = serial_port.read(1)

    # Wczytanie drugiego bajtu pakietu
    block_number = serial_port.read(1)
    # Zamienianie odczytanego bajtu na int.
    number_as_integer = int.from_bytes(block_number, "big")

    # Odczytywanie trzeciego bajtu.
    completion_number = serial_port.read(1)
    completion_number_as_integer = int.from_bytes(completion_number, "big")

    if len(header) == 0:
        return 3
    elif header == var.EOT:
        return 2
    elif header != var.SOH:
        return 1

    # Sprawdzanie numeru pakietu.
    if packet_number % 255 != number_as_integer:
        return 1

    # Sprawdzenie, czy dopełnienie jest wysłane prawidłowo.
    if 255 - (packet_number % 255) != completion_number_as_integer:
        return 1

    return 0


# Usuwanie znaków SUB z końca wiadomości.
def removeGarbage(data: bytes):
    data = bytearray(data)
    while data[-1] == 26:
        del data[-1]
    return data
