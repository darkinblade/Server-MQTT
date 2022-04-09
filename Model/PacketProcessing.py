from struct import *

from Model.Tools import *


def processPackage(package, data):
    switcher = {
        PacketType.CONNECT: CONNECT,
        PacketType.CONNACK: CONNACK,
        PacketType.PUBLISH: PUBLISH,
        PacketType.PUBACK: PUBACK,
        PacketType.PUBREC: PUBREC,
        PacketType.PUBREL: PUBREL,
        PacketType.PUBCOMP: PUBCOMP,
        PacketType.SUBSCRIBE: SUBSCRIBE,
        PacketType.SUBACK: SUBACK,
        PacketType.UNSUBSCRIBE: UNSUBSCRIBE,
        PacketType.UNSUBACK: UNSUBACK,
        PacketType.PINGREQ: PINGREQ,
        PacketType.PINGRESP: PINGRESP,
        PacketType.DISCONNECT: DISCONNECT,
    }
    func = switcher.get(package.type)
    return func(package, data)


def CONNECT(package, data):
    formString = '12c'

    _, _, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10 = unpack(formString, data[0: 12])

    if not (
            b1 == b'\x00' and b2 == b'\x04' and b3 == b'M' and b4 == b'Q' and b5 == b'T' and b6 == b'T' and b7 == b'\x04'):
        raise RuntimeError('Protocol Name invalid')

    b8_int = int.from_bytes(b8, byteorder='big', signed=False)

    if not (b8_int & 1 == 0):
        raise RuntimeError('Bitul reserved nu este 0, cerem deconectarea clientului')

    if b8_int & 2 == 2:
        package.clearSession = True
    else:
        package.clearSession = False

    if b8_int & 4 == 4:
        package.will_flag = True

        if b8_int & 32 == 32:
            package.will_retain = True
        else:
            package.will_retain = False
    else:
        package.will_flag = False
        package.will_retain = False

    if b8_int & 24 < 24:
        if b8_int & 24 <= 7:
            package.will_qos = 0
        elif b8_int & 24 <= 15:
            package.will_qos = 1
        elif b8_int & 24 <= 23:
            package.will_qos = 2
    else:
        pass

    if b8_int & 128 == 128:
        package.username_flag = True
    else:
        package.username_flag = False
        package.password_flag = False

    if b8_int & 64 == 64:
        package.password_flag = True
    else:
        package.password_flag = False

    package.keep_alive = int.from_bytes(b9 + b10, byteorder='big', signed=False)

    print("Keep alive =", package.keep_alive, "secunde")

    pointer = 12

    b11, b12 = unpack('cc', data[pointer: pointer + 2])
    client_id_length = int.from_bytes(b11 + b12, byteorder='big', signed=False)

    pointer = pointer + 2
    package.client_id += data[pointer:pointer + client_id_length].decode("utf-8")
    print(f'Client id: {package.client_id}')

    pointer = pointer + client_id_length

    if package.will_flag:
        b13, b14 = unpack('cc', data[pointer: pointer + 2])
        will_topic_length = int.from_bytes(b13 + b14, byteorder='big', signed=False)
        pointer = pointer + 2
        package.will_topic += data[pointer:pointer + will_topic_length].decode("utf-8")
        print(f'Client will topic: {package.will_topic}')

        pointer = pointer + will_topic_length

        b15, b16 = unpack('cc', data[pointer: pointer + 2])
        will_message_length = int.from_bytes(b15 + b16, byteorder='big', signed=False)
        pointer = pointer + 2
        package.will_message += data[pointer:pointer + will_message_length].decode("utf-8")
        print(f'Client will message: {package.will_message}')

        pointer = pointer + will_message_length

    if package.username_flag:
        b17, b18 = unpack('cc', data[pointer: pointer + 2])
        username_length = int.from_bytes(b17 + b18, byteorder='big', signed=False)
        pointer = pointer + 2
        package.username += data[pointer:pointer + username_length].decode("utf-8")
        print(f'Client username: {package.username}')

        pointer = pointer + username_length

    if package.password_flag:
        b19, b20 = unpack('cc', data[pointer: pointer + 2])
        password_length = int.from_bytes(b19 + b20, byteorder='big', signed=False)
        pointer = pointer + 2
        package.password += data[pointer:pointer + password_length].decode("utf-8")
        print(f'Client password: {package.password}')


def CONNACK(package, data):
    pass


def PUBLISH(package, data):
    formString = 'cccc'
    b1, b2, b3, b4 = unpack(formString, data[0: 4])
    b1_int = int.from_bytes(b1, byteorder='big', signed=False)
    b2_int = int.from_bytes(b2, byteorder='big', signed=False)

    package.dup = b1_int & 8
    print("DUP flag = ", package.dup)

    if b1_int & 6 < 6:
        if b1_int & 6 <= 1:
            print("Avem QoS=0")
            package.QoS = 0
        elif b1_int & 6 <= 3:
            print("Avel QoS=1")
            package.QoS = 1
        elif b1_int & 6 <= 5:
            print("Avem QoS=2")
            package.QoS = 2
    else:
        print("QoS invalid (=3), inchidem conexiunea")

    package.retain = b1_int & 1

    topic_name_length = int.from_bytes(b3 + b4, byteorder='big', signed=False)
    fmt = str(topic_name_length + (2 if package.QoS > 0 else 0)) + 'c'
    tuple_pub = unpack(fmt, data[4:4 + topic_name_length + (2 if package.QoS > 0 else 0)])

    package.topicName = ""
    for x in range(0, topic_name_length):
        package.topicName += tuple_pub[x].decode("utf-8")
    print("Topic name:", package.topicName)

    package.packetIdentifier = ""
    if package.QoS > 0:
        package.packetIdentifier = int.from_bytes(tuple_pub[topic_name_length] + tuple_pub[topic_name_length + 1],
                                                  byteorder='big', signed=False)
    print("Packet ID:", package.packetIdentifier)

    brah = 4 + topic_name_length + (2 if package.QoS > 0 else 0)
    fmt = str(b2_int - brah + 2) + 'c'
    message = unpack(fmt, data[brah: b2_int + 2])

    for x in range(0, b2_int - brah + 2):
        package.message += message[x].decode("utf-8")
    print("Publish message:", package.message)


def PUBACK(package, data):
    pass


def PUBREC(package, data):
    pass


def PUBREL(package, data):
    form = 'cccc'
    b1, b2, b3, b4 = unpack(form, data[0: 4])
    package.packetIdentifier = int.from_bytes(b3 + b4, byteorder='big', signed=False)


def PUBCOMP(package, data):
    pass


def SUBSCRIBE(package, data):
    formString = 'cccc'

    _, _, b1, b2, = unpack(formString, data[0: 4])
    package.packetIdentifier = int.from_bytes(b1 + b2, "big", signed=False)

    dataPointer = 4

    topicSize = int.from_bytes(data[dataPointer:dataPointer + 2], "big", signed=False)
    print(f"My topic size is {topicSize}")

    startOfTopicPointer = dataPointer + 2
    endOfTopicPointer = topicSize + startOfTopicPointer

    topicName = data[startOfTopicPointer:endOfTopicPointer].decode("utf-8")
    topicQoS = data[endOfTopicPointer]

    package.topicList.append(topicName)
    package.topicQoS[topicName] = topicQoS
    print(f"My topic is {topicName}")

    dataPointer = endOfTopicPointer


def SUBACK(package, data):
    pass


def UNSUBSCRIBE(package, data):
    formString = 'cccc'

    _, _, b1, b2, = unpack(formString, data[0: 4])
    package.packetIdentifier = int.from_bytes(b1 + b2, "big", signed=False)

    dataPointer = 4

    topicSize = int.from_bytes(data[dataPointer:dataPointer + 2], "big", signed=False)
    print(f"My unsubcribe topic size is {topicSize}")

    startOfTopicPointer = dataPointer + 2
    endOfTopicPointer = topicSize + startOfTopicPointer

    topicName = data[startOfTopicPointer:endOfTopicPointer].decode("utf-8")
    package.topicList.append(topicName)
    print(f"My unsubcribe topic is {topicName}")


def UNSUBACK(package, data):
    pass


def PINGREQ(package, data):
    pass


def PINGRESP(package, data):
    pass


def DISCONNECT(package, data):
    pass
