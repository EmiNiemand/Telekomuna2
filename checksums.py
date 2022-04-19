from numpy import char
import variables as var


def checksumAlgebraic(block: bytes):
    result = 0
    for i in block:
        result += i
    result = result % 256
    return result.to_bytes(1, "big")


def checksumCRC(block: bytes):
    crc = 0
    for byte in block:
        crc = ((crc << 8) & 0xff00) ^ var.CRC16_TABLE[((crc >> 8) & 0xff) ^ byte]
    return crc.to_bytes(2, "big")


# Obliczanie checksumy.
def calculateChecksum(data_block: bytes, check_sum_type: char):
    if check_sum_type == var.NAK:
        return checksumAlgebraic(data_block)
    else:
        return checksumCRC(data_block)
