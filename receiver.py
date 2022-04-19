from numpy import char
import serial as ser
import variables as var
import checksums as che

#====================Exceptions======================
class NoAcceptFromSenderException(Exception):
    pass


class ACKException(Exception):
    pass


class NAKException(Exception):
    pass


class InvalidChecksumException(NAKException):
    pass


class InvalidHeaderException(NAKException):
    pass


class WrongPacketNumberException(NAKException):
    pass


#===========================Functions==================
def receiveMessage(serial_port: ser.Serial, check_sum_type: char):
    message = bytearray()
    for i in range(20):
        # Wysyłanie jakiego rodzaju pakiety chcę otrzymywać.
        serial_port.write(check_sum_type)
        packet_number = 1
        while True:
            try:
                # Sprawdzanie poprawności pakietu
                block_of_data = checkPacket(serial_port, packet_number, check_sum_type)
                # Zapisuje kolejne części wiadomości do rozwiązania.
                message += bytearray(block_of_data)
                # Zwraca znak ACK do nadawcy.
                serial_port.write(var.ACK)
                packet_number += 1
            except NAKException:
                # Czyszczenie portu
                # Jeśli nie odczytany pakiet nie jest prawidłowy, to wyślij NAK,
                # żeby pakiet został wysłany jeszcze raz.
                serial_port.read(serial_port.in_waiting)
                serial_port.write(var.NAK)
            except ACKException:
                # Zakończenie transferu i zwrócenie wiadomości.
                serial_port.write(var.ACK)
                return bytes(message)
            except NoAcceptFromSenderException:
                # Jeżeli transfer nie został zaakceptowany lub skończył się czas nasłuchiwania.
                raise NoAcceptFromSenderException

    raise NoAcceptFromSenderException


def checkPacket(serial_port: ser.Serial, packet_number: int, check_sum_type: char):
    # sprawdzanie poprawności nagłówka.
    checkHeader(serial_port, packet_number)
    # Odczytanie bajtów wiadomości.
    data_block = serial_port.read(128)

    # Odczytanie checksumy.
    if check_sum_type == var.NAK:
        message_checksum = serial_port.read(1)
    elif check_sum_type == var.C:
        message_checksum = serial_port.read(2)

    # Sprawdzanie czy odczytana checksuma jest równa obliczonej na podstawie bloku wiadomości.
    calculated_checksum = che.calculateChecksum(data_block, check_sum_type)

    if message_checksum != calculated_checksum:
        raise InvalidChecksumException

    return data_block


def checkHeader(serial_port: ser.Serial, packet_number: int):
    # Sprawdzanie czy pierwszy bajt jest równy znakowi SOH.
    header = serial_port.read(1)

    # Wczytanie drugiego bajtu pakietu
    block_number = serial_port.read(1)
    # Zamienianie odczytanego bajtu na int.
    number_as_integer = int.from_bytes(block_number, "big")

    # Odczytywanie trzeciego bajtu.
    completion_number = serial_port.read(1)
    completion_number_as_integer = int.from_bytes(completion_number, "big")

    if len(header) == 0:
        raise NoAcceptFromSenderException
    elif header == var.EOT:
        raise ACKException
    elif header != var.SOH:
        raise InvalidHeaderException

    # Sprawdzanie numeru pakietu.
    if packet_number % 255 != number_as_integer:
        raise WrongPacketNumberException

    # Sprawdzenie czy dopełnienie jest wysłane prawidłowo.
    if 255 - (packet_number % 255) != completion_number_as_integer:
        raise WrongPacketNumberException

    return bytearray(header) + bytearray(block_number) + bytearray(completion_number_as_integer)


# Usuwanie znaków SUB z końca wiadomości.
def removeGarbage(data: bytes):
    data = bytearray(data)
    while data[-1] == 26:
        del data[-1]
    return data

