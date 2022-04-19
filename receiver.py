from numpy import char
import serial as ser
import variables as var
import checksums as che


class NAKException(Exception):
    pass


class ACKException(Exception):
    pass


class NoAcceptFromSenderException(Exception):
    pass


class InvalidChecksumException(NAKException):
    pass


class InvalidHeaderException(NAKException):
    pass


class WrongPacketNumberException(NAKException):
    pass


# Usuwanie znaków SUB z końca wiadomości.
def removeGarbage(data: bytes):
    data = bytearray(data)
    while data[-1] == 26:
        del data[-1]
    return data


def receiveMessage(serial_port: ser.Serial, check_sum_type: char):
    result = bytearray()
    for i in range(20):
        # Wysyłanie jakiego rodzaju pakiety chcę otrzymywać.
        serial_port.write(check_sum_type)
        packet_number = 1
        while True:
            try:
                # Sprawdzanie poprawności pakietu
                data_block = checkPacket(serial_port, packet_number, check_sum_type)
                # Zapisuje kolejne części wiadomości do rozwiązania.
                result += bytearray(data_block)
                # Zwraca znak ACK do nadawcy.
                serial_port.write(var.ACK)
                packet_number += 1
            except NAKException:
                # Jeśli nie odczytany pakiet nie jest prawidłowy, to wyślij NAK,
                # żeby pakiet został wysłany jeszcze raz.
                serial_port.read(serial_port.in_waiting)
                serial_port.write(var.NAK)
            except ACKException:
                # Zakończenie transferu i zwrócenie wiadomości.
                serial_port.write(var.ACK)
                return bytes(result)
            except NoAcceptFromSenderException:
                # Jeżeli transfer nie został zaakceptowany lub skończył się czas nasłuchiwania.
                break

    raise NoAcceptFromSenderException


def checkPacket(serial_port: ser.Serial, packet_number: int, check_sum_type: char):
    # sprawdzanie poprawności nagłówka.
    checkHeader(serial_port, packet_number)
    # Odczytanie bajtów wiadomości.
    data_block = serial_port.read(128)

    # Odczytanie checksumy.
    if check_sum_type == var.NAK:
        message_sum = serial_port.read(1)
    else:
        message_sum = serial_port.read(2)

    # Sprawdzanie czy odczytana checksuma jest równa obliczonej na podstawie bloku wiadomości.
    calculated_sum = che.calculateChecksum(data_block, check_sum_type)

    if message_sum != calculated_sum:
        raise InvalidChecksumException

    return data_block


def checkHeader(serial_port: ser.Serial, packet_number: int):
    # Sprawdzanie czy pierwszy bajt jest równy znakowi SOH.
    header = serial_port.read(1)

    if len(header) == 0:
        raise NoAcceptFromSenderException
    elif header == var.EOT:
        raise ACKException
    elif header != var.SOH:
        raise InvalidHeaderException

    # Wczytanie drugiego bajtu pakietu
    message_number = serial_port.read(1)
    # Zamienianie odczytanego bajtu na int.
    message_number_integer = int.from_bytes(message_number, "big")

    # Sprawdzanie numeru pakietu.
    if packet_number % 255 != message_number_integer:
        raise WrongPacketNumberException

    # Odczytywanie trzeciego bajtu.
    message_number_completion = serial_port.read(1)
    message_number_completion_integer = int.from_bytes(message_number_completion, "big")

    # Sprawdzenie czy dopełnienie jest wysłane prawidłowo.
    if 255 - (packet_number % 255) != message_number_completion_integer:
        raise WrongPacketNumberException

    return bytearray(header) + bytearray(message_number) + bytearray(message_number_completion)
