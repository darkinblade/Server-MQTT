import struct

from Model.Tools import *


def createPackage(package):
    if package.type == PacketType.CONNACK:
        return createCONNACK(package)
    elif package.type == PacketType.SUBACK:
        return createSUBACK(package)
    elif package.type == PacketType.PINGRESP:
        return createPINGRESP(package)
    elif package.type == PacketType.PINGREQ:
        return createPINGREQ(package)
    elif package.type == PacketType.PUBLISH:
        return createPUBLISH(package)
    elif package.type == PacketType.PUBACK:
        return createPUBACK(package)
    elif package.type == PacketType.PUBREL:
        return createPUBREL(package)
    elif package.type == PacketType.PUBREC:
        return createPUBREC(package)
    elif package.type == PacketType.PUBCOMP:
        return createPUBCOMP(package)


def createSUBACK(package):
    format = "ccccc"

    identifier = package.packetIdentifier.to_bytes(2, 'big')
    data = struct.pack(format, b'\x90', b'\x03', identifier[0:1], identifier[1:2], b'\x00')
    return data


def createCONNACK(package):
    SP = b'\x00'

    format = "cccc"

    if package.clearSession:
        SP = b'\x00'
    else:
        if package.sessionAlreadyExisted:
            SP = b'\x01'
        else:
            SP = b'\x00'

    data = struct.pack(format, b'\x20', b'\x02', SP, b'\x00')
    return data


def createPINGREQ(package):
    data = struct.pack("2c", b'\xC0', b'\x00')
    return data


def createPINGRESP(package):
    data = struct.pack("2c", b'\xD0', b'\x00')
    return data


def createPUBLISH(package):
    b1_int = 48

    if package.dup:
        set_bit(b1_int, 3)

    if package.QoS == 2:
        set_bit(b1_int, 2)
        set_bit(b1_int, 1)
    elif package.QoS == 1:
        set_bit(b1_int, 1)

    if package.retain:
        set_bit(b1_int, 0)

    b1 = (b1_int).to_bytes(1, 'big')

    topicSize = len(package.topicName)
    variableHeader = topicSize.to_bytes(2, 'big')
    variableHeader += package.topicName.encode('UTF-8')

    if package.QoS > 0:
        variableHeader += struct.pack("cc", b'\xD1', b'\xD3')

    variableHeader += package.message.encode('UTF-8')

    b2 = (len(variableHeader)).to_bytes(1, 'big')
    data = struct.pack("cc", b1, b2)
    data += variableHeader

    return data


def createPUBACK(package):
    data = struct.pack("4c", b'\x40', b'\x02', package.packetIdentifier.to_bytes(2, 'big')[0:1],
                       package.packetIdentifier.to_bytes(2, 'big')[1:2])
    return data


def createPUBREC(package):
    data = struct.pack("4c", b'\x50', b'\x02', package.packetIdentifier.to_bytes(2, 'big')[0:1],
                       package.packetIdentifier.to_bytes(2, 'big')[1:2])
    return data


def createPUBREL(package):
    data = struct.pack("4c", b'\x62', b'\x02', package.packetIdentifier.to_bytes(2, 'big')[0:1],
                       package.packetIdentifier.to_bytes(2, 'big')[1:2])
    return data


def createPUBCOMP(package):
    data = struct.pack("4c", b'\x70', b'\x02', package.packetIdentifier.to_bytes(2, 'big')[0:1],
                       package.packetIdentifier.to_bytes(2, 'big')[1:2])
    return data


def set_bit(value, bit):
    return value | (1 << bit)


def clear_bit(value, bit):
    return value & ~(1 << bit)
