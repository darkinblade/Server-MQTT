from Model.FixedHeader import ProcessFixedHeader
from Model.PacketFactory import createPackage
from Model.PacketProcessing import *


class Package:
    def __init__(self):
        self.type = None

        self.dup = False
        self.QoS = None
        self.retain = False
        self.packetIdentifier = 0
        self.client_id = ''

        self.topicList = list()
        self.topicQoS = dict()

        self.clearSession = None

        self.will_flag = None
        self.will_retain = None
        self.will_qos = None
        self.will_message = ''
        self.will_topic = ''

        self.username_flag = None
        self.password_flag = None
        self.username = ''
        self.password = ''

        self.keep_alive = None

        self.sessionAlreadyExisted = False

        self.message = ""
        self.topicName = ""

    def deserialize(self, data):
        self.type = ProcessFixedHeader(data)
        processPackage(self, data)

    def serialize(self):
        return createPackage(self)


def readPackage(socket):
    packageBites = b''
    try:
        packageBites += socket.recv(2)

        if packageBites:
            remainingLengthOfPackage = packageBites[1]
        else:
            return 0

        packageBites += socket.recv(remainingLengthOfPackage)

        return packageBites
    except Exception:
        raise Exception("Socket failed")
