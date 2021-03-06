from Model.Tools import PacketType


class HeaderException(Exception):
    def __init__(self, message="Header invalid"):
        self.message = message
        super().__init__(self.message)


def ProcessFixedHeader(fixedHeader):
    switcher = {
        16: CONNECT,  # 1
        32: CONNACK,  # 2
        48: PUBLISH,  # 3
        64: PUBACK,  # 4
        80: PUBREC,  # 5
        96: PUBREL,  # 6
        112: PUBCOMP,  # 7
        128: SUBSCRIBE,  # 8
        144: SUBACK,  # 9
        160: UNSUBSCRIBE,  # 10
        176: UNSUBACK,  # 11
        192: PINGREQ,  # 12
        208: PINGRESP,  # 13
        224: DISCONNECT,  # 14
    }

    brah = fixedHeader[0]
    brah2 = brah & 240
    func = switcher.get(brah2, ERROR)

    return func(fixedHeader[0])


def ERROR(fh):
    print("ERROR")
    raise HeaderException()


def CONNECT(fh):
    ValidateZero(fh)
    print("CONNECT")
    return PacketType.CONNECT


def CONNACK(fh):
    ValidateZero(fh)
    print("CONNACK")
    return PacketType.CONNACK


def PUBLISH(fh):
    print("PUBLISH")
    return PacketType.PUBLISH


def PUBACK(fh):
    ValidateZero(fh)
    print("PUBACK")
    return PacketType.PUBACK


def PUBREC(fh):
    ValidateZero(fh)
    print("PUBREC")
    return PacketType.PUBREC


def PUBREL(fh):
    ValidateOne(fh)
    print("PUBREL")
    return PacketType.PUBREL


def PUBCOMP(fh):
    ValidateZero(fh)
    print("PUBCOMP")
    return PacketType.PUBCOMP


def SUBSCRIBE(fh):
    ValidateOne(fh)
    print("SUBSCRIBE")
    return PacketType.SUBSCRIBE


def SUBACK(fh):
    ValidateZero(fh)
    print("SUBACK")
    return PacketType.SUBACK


def UNSUBSCRIBE(fh):
    ValidateOne(fh)
    print("UNSUBSCRIBE")
    return PacketType.UNSUBSCRIBE


def UNSUBACK(fh):
    ValidateZero(fh)
    print("UNSUBACK")
    return PacketType.UNSUBACK


def PINGREQ(fh):
    ValidateZero(fh)
    print("PINGREQ")
    return PacketType.PINGREQ


def PINGRESP(fh):
    ValidateZero(fh)
    print("PINGRESP")
    return PacketType.PINGRESP


def DISCONNECT(fh):
    ValidateZero(fh)
    print("DISCONNECT")
    return PacketType.DISCONNECT


def ValidateZero(byte):
    byte = byte & 15
    if (byte != 0):
        raise HeaderException()


def ValidateOne(byte):
    byte = byte & 15
    if (byte != 2):
        raise HeaderException()
