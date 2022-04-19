import portInitialize as por
import variables as var
import sender as sen
import receiver as rec


def main():
    menu = int(input("Wpisz '1' żeby wysłać, albo '2' żeby odebrać: "))
    port_number = "COM"
    port_number += input("Podaj numer portu: ")
    text = ""
    if menu == 1:
        with open('message') as f:
            lines = f.readlines()
        for line in lines:
            text += line
        serial_port = por.startSerialPort(port_number)
        sen.sendMessage(serial_port, bytes(text, 'ascii'))
        serial_port.close()
    elif menu == 2:
        checksum_type = int(input("Wpisz '1' - algebraiczna suma kontrolna, '2' - CRC: "))
        if checksum_type == 1:
            checksum_type = var.NAK
        elif checksum_type == 2:
            checksum_type = var.C
        else:
            raise Exception
        serial_port = por.startSerialPort(port_number)
        data = rec.receiveMessage(serial_port, checksum_type)
        data = bytes(rec.removeGarbage(data))
        print(data.decode("utf-8"))
        serial_port.close()


if __name__ == '__main__':
    main()

