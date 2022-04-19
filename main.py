import portInitialize as por
import variables as var
import sender as sen
import receiver as rec


def main():
    menu = int(input("Podaj 1 żeby wysłać, albo 2 żeby odebrać: "))
    port_number = "COM"
    port_number += input("Podaj numer portu: ")

    if menu == 1:
        with open('message') as f:
            lines = f.readlines()

        serial_port = por.startSerialPort(port_number)
        sen.send(serial_port, bytes(lines[0], 'ascii'))
        serial_port.close()
    elif menu == 2:
        serial_port = por.startSerialPort(port_number)
        data = rec.receive(serial_port, var.NAK)
        data = bytes(rec.removeGarbage(data))
        print(data.decode("utf-8"))
        serial_port.close()


if __name__ == '__main__':
    main()

