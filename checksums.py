import variables as var
import port_initialize as pi

def algebraic_check_sum(block: bytes):
    result = 0
    for i in block:
        result += i
    result = result % 256
    return result.to_bytes(1, "big")


def crc_check_sum(block: bytes):
    crc = 0
    for byte in block:
        crc = ((crc << 8) & 0xff00) ^ var.CRC16_TABLE[((crc >> 8) & 0xff) ^ byte]
    return crc.to_bytes(2, "big")


def calculate_checksum(data_block: bytes, check_sum_type: pi.ChecksumEnum):
    if check_sum_type == pi.ChecksumEnum.algebraic:
        return algebraic_check_sum(data_block)
    else:
        return crc_check_sum(data_block)
