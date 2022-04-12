class TransferNotStartedException(Exception):
    pass


class SenderNotAcceptedTransferException(Exception):
    pass


class NAKException(Exception):
    pass


class WrongPacketNumberException(NAKException):
    pass


class InvalidChecksumException(NAKException):
    pass


class InvalidHeaderException(NAKException):
    pass


class EOTHeaderException(Exception):
    pass


class UnexpectedResponseException(Exception):
    pass