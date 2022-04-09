import time

from Model.Autentification import checkPassword
from Model.Client import Client
from Model.Package import Package
from Model.Session import Sesion
from Model.Tools import *


class ClientManager:

    def __init__(self, server):

        self.server = server

        self.activeClients = dict()
        self.persistentSessions = dict()

        self.retainMessages = dict()
        self.savedMessages = dict()
        self.topicEntry = dict()

        self.unacknowledgedMessages = list()

    def applyPackage(self, package, mySocket):
        if mySocket in self.activeClients:
            self.activeClients[mySocket].resetTime()

        if package.type == PacketType.CONNECT:
            self.ProcessConnect(package, mySocket)
        elif package.type == PacketType.SUBSCRIBE:
            self.ProcessSubscribe(package, mySocket)
        elif package.type == PacketType.PUBLISH:
            self.ProcessPublish(package, mySocket)
        elif package.type == PacketType.PUBACK:
            self.ProcessPUBACK(package, mySocket)
        elif package.type == PacketType.DISCONNECT:
            self.ProcessDisconnected(package, mySocket)
        elif package.type == PacketType.PINGREQ:
            self.ProcessPINGREQ(package, mySocket)
        elif (package.type == PacketType.UNSUBSCRIBE):
            self.ProcessUNSUBSCRIBE(package, mySocket)
        elif package.type == PacketType.PUBREL:
            self.ProcessPUBREL(package, mySocket)
        elif package.type == PacketType.PUBREC:
            self.ProcessPUBREC(package, mySocket)
        elif package.type == PacketType.PUBCOMP:
            self.ProcessPUBCOMP(package, mySocket)
        elif (package.type == PacketType.PINGRESP):
            self.server.logs.insert(0, f"Received ping from client.")

    def keepAliveCheck(self):
        for client in self.activeClients.values():
            if client.ext_deadline <= time.time():
                self.clientSocketFailed(client.associatedSocket)

    def ProcessConnect(self, package, mySocket):
        sessionAlreadyExisted = False

        if mySocket in self.activeClients:
            raise "This client has not been properly disconected last time."

        newClient = Client(package.client_id, mySocket, package.keep_alive)
        self.activeClients[mySocket] = newClient  # Fiecare client este asociat strict unui socket

        if package.clearSession:
            if package.client_id in self.persistentSessions:
                del self.persistentSessions[package.client_id]

            newSession = Sesion(persistent=False)
            newClient.associatedSession = newSession
        else:
            if package.client_id not in self.persistentSessions:
                newSession = Sesion(persistent=True)
                newClient.associatedSession = newSession
                self.persistentSessions[package.client_id] = newSession
            else:
                sessionAlreadyExisted = True
                newClient.associatedSession = self.persistentSessions[package.client_id]

        ##AUTENTIFICATION
        if package.password_flag and package.username_flag:
            if checkPassword(package.username, bytes(package.password, 'utf-8')):
                newClient.authenticated = True
                self.server.logs.insert(0, f"Client authentication successful.")

            else:
                self.server.logs.insert(0, f"Client authentication successful.")

        newClient.resetTime()

        if package.will_flag:
            newClient.willFlag = True
            newClient.willTopic = package.will_topic
            newClient.willMessage = package.will_message
            newClient.willQoS = package.will_qos

        newPackage = Package()
        newPackage.type = PacketType.CONNACK

        newPackage.clearSession = package.clearSession
        newPackage.sessionAlreadyExisted = sessionAlreadyExisted

        data = newPackage.serialize()
        mySocket.send(data)

        self.server.tree.event_generate("<<CONNECT>>")

    def ProcessSubscribe(self, package, mySocket):

        ourClient = self.activeClients[mySocket]
        for topic in package.topicList:
            ourClient.associatedSession.addTopic(topic, package.topicQoS[topic])

        newPackage = Package()
        newPackage.type = PacketType.SUBACK
        newPackage.packetIdentifier = package.packetIdentifier
        data = newPackage.serialize()
        mySocket.send(data)

        for topic in package.topicList:

            if topic in self.retainMessages:
                if self.retainMessages[topic][0] != '':
                    self.publishRetainMessage(topic, self.retainMessages[topic], mySocket)

            if topic not in self.topicEntry:
                self.topicEntry[topic] = list()
        self.server.logs.insert(0,
                                f"Client {self.activeClients[mySocket].clientID} subscribed to topic {package.topicList}.")

        self.server.tree.event_generate("<<SUBSCRIBE>>")

    def ProcessUNSUBSCRIBE(self, package, mySocket):
        ourClient = self.activeClients[mySocket]
        ourClient.associatedSession.removeTopics(package.topicList)

    def ProcessPublish(self, package, mySocket):
        self.server.logs.insert(0, f"Received PUBLISH packet from {self.activeClients[mySocket].clientID}.")

        if package.QoS == 0:
            self.publishMessage(package.topicName, package.message, package.QoS)

        if package.QoS == 1:
            self.savedMessages[mySocket] = package.packetIdentifier
            self.publishMessage(package.topicName, package.message, package.QoS)
            newPackage = Package()
            newPackage.type = PacketType.PUBACK
            newPackage.packetIdentifier = package.packetIdentifier

            data = newPackage.serialize()
            mySocket.send(data)

        if package.QoS == 2:
            self.savedMessages[mySocket] = package.packetIdentifier
            self.publishMessage(package.topicName, package.message, package.QoS)
            newPackage = Package()
            newPackage.type = PacketType.PUBREC
            newPackage.packetIdentifier = package.packetIdentifier

            data = newPackage.serialize()
            mySocket.send(data)

        self.addInDict(self.topicEntry, package.topicName, package.message)

        if package.retain:
            self.retainMessages[package.topicName] = (package.message, package.QoS)

        self.server.tree.event_generate("<<PUBLISH>>")

    def ProcessPUBACK(self, package, mySocket):
        for key in self.savedMessages.keys():
            if key.values() == package.packetIdentifier:
                self.savedMessages.pop(key, None)

    def ProcessPUBREL(self, package, mySocket):
        newPackage = Package()
        newPackage.type = PacketType.PUBCOMP
        newPackage.packetIdentifier = package.packetIdentifier

        data = newPackage.serialize()
        mySocket.send(data)
        self.server.logs.insert(0,
                                f"Received PUBREL from {self.activeClients[mySocket].clientID}, responded with PUBCOMP.")

    def ProcessPUBCOMP(self, package, mySocket):

        self.server.logs.insert(0,
                                f"Received PUBCOMP from {self.activeClients[mySocket].clientID}.")

    def ProcessPUBREC(self, package, mySocket):
        for key in self.savedMessages.keys():
            if key.values() == package.packetIdentifier:
                self.savedMessages.pop(key, None)

        newPackage = Package()
        newPackage.type = PacketType.PUBREL
        newPackage.packetIdentifier = package.packetIdentifier

        data = newPackage.serialize()
        mySocket.send(data)
        self.server.logs.insert(0,
                                f"Received PUBREC from {self.activeClients[mySocket].clientID}, responded with PUBREL.")

    def ProcessPINGREQ(self, package, mySocket):
        newPackage = Package()
        newPackage.type = PacketType.PINGRESP
        data = newPackage.serialize()
        mySocket.send(data)
        self.server.logs.insert(0,
                                f"Received PINGREQ from {self.activeClients[mySocket].clientID}, responded with PINGRESP.")

    def ProcessDisconnected(self, package, mySocket):
        self.activeClients[mySocket].safelyDisconnected = True
        self.clientSafelyDisconnected(mySocket)

    # _________________________UTILITY FUNCTIONS_________________________

    def publishMessage(self, topicName, message, qos):
        for client in self.activeClients.values():

            session = client.associatedSession

            if topicName in session.subscribedTopics:

                newPackage = Package()
                newPackage.type = PacketType.PUBLISH
                newPackage.topicName = topicName
                newPackage.message = message
                newPackage.QoS = qos

                data = newPackage.serialize()

                try:
                    client.associatedSocket.send(data)
                except:
                    pass

        self.server.logs.insert(0,
                                f"Sent PUBLISH packet with the topic '{topicName}',the message '{message}' and QoS {qos}.")

    def publishRetainMessage(self, topicName, retainMessage, mySocket):
        newPackage = Package()
        newPackage.type = PacketType.PUBLISH
        newPackage.topicName = topicName
        newPackage.message = retainMessage[0]
        newPackage.retain = True
        newPackage.QoS = retainMessage[1]

        data = newPackage.serialize()
        mySocket.send(data)
        self.server.logs.insert(0,
                                f"Published retain message {retainMessage[0]}, topic {topicName} and QoS {retainMessage[1]}.")

    def clientSafelyDisconnected(self, mySocket):
        self.server.logs.insert(0, f"Client {self.activeClients[mySocket].clientID} successfully disconnected.")
        self.server.removeSocketFromList(mySocket)  # This is important is we don't want the select to go wild
        mySocket.close()
        self.activeClients.pop(mySocket)
        self.server.tree.event_generate("<<DISCONNECT>>")

    def clientSocketFailed(self, mySocket):

        try:
            client = self.activeClients[mySocket]

            if client.willFlag:
                self.publishMessage(client.willTopic, client.willMessage, client.willQoS)
                self.server.logs.insert(0,
                                        f"Client {self.activeClients[mySocket].clientID} Last Will message:{client.willMessage}.")

            self.server.removeSocketFromList(mySocket)  # Eradicate the socket from the server list as well
            mySocket.close()
            self.activeClients.pop(mySocket)  # Delete the client

            self.server.logs.insert(0, f"Client {self.activeClients[mySocket].clientID} unexpectedly disconnected.")
        except:
            pass

    def addInDict(self, dict, key, values):
        if key not in dict:
            dict[key] = list()
        dict[key].append(str(values))
        return dict
