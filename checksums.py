from numpy import char
import variables as var

# algebraiczna suma kontrolna
def checksumAlgebraic(block: bytes):
    result = 0
    for i in block:
        result += i
    result = result % 256
    return result.to_bytes(1, "big")

# suma kontrolna CRC
def checksumCRC(block: bytes):
    crc = 0
    for byte in block:
        crc = ((crc << 8) & 0xff00) ^ var.CRC16_TABLE[((crc >> 8) & 0xff) ^ byte]
    return crc.to_bytes(2, "big")


# Obliczanie checksumy w zależności od znaku
def calculateChecksum(data_block: bytes, check_sum_type: char):
    if check_sum_type == var.NAK:
        return checksumAlgebraic(data_block)
    elif check_sum_type == var.C:
        return checksumCRC(data_block)
