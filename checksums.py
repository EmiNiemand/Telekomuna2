import variables as v

def algebraic_checksum(block: bytes):
    result = 0
    for byte in block:
        result += byte
    result = result % 256
    return result.to_bytes(1, 'big')


def crc_checksum(block: bytes):
    crc = 0
    for byte in block:
        crc = ((crc << 8) & 0xff00) ^ v.CRC16_TABLE[((crc >> 8) & 0xff) ^ byte]
    return crc.to_bytes(2, 'big')

