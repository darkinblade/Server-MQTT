import select
import socket
import threading

from Model.ClientManager import ClientManager
from Model.Package import Package, readPackage
from Model.Tools import settings

FORMAT = 'utf-8'


class MQTTServer:

    def __init__(self, tree, logs):
        settings.debugMode = False

        self.port = 1883

        self.socketList = list()
        self.clientManager = None

        self.running = False

        self.serverIP = 0
        self.serverSocket = None
        self.serverThread = None
        self.receiveThread = None
        self.tree = tree
        self.logs = logs

        hostname = socket.gethostname()
        self.serverIP = socket.gethostbyname(hostname)

        self.logs.insert(0, f"Server has taked IP: {self.serverIP}")

        self.addr = (self.serverIP, self.port)

        self.clientManager = ClientManager(self)

        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serverSocket.bind(self.addr)

            self.serverThread = threading.Thread(target=self.startServer, args=())
            self.serverThread.start()

            self.receiveThread = threading.Thread(target=self.handleClients, args=())
            self.receiveThread.start()
        except BaseException as err:
            self.logs.insert(0, f"Unexpected {err=}, {type(err)=} is server startup.")
            raise
        else:
            self.logs.insert(0, f"Server bound on port {self.port} is starting.")

            self.running = True

    def startServer(self):
        try:
            self.serverSocket.listen()
        except BaseException as err:
            self.logs.insert(0, f"Unexpected {err=}, {type(err)=}.Thread is quitting.")
            return

        self.logs.insert(0, f"Server is listening on {self.addr}\n")

        while True:

            try:
                conn, addr = self.serverSocket.accept()

                self.socketList.append(conn)

            except OSError as err:
                self.running = False
                break
            except BaseException as err:
                self.logs.insert(0, f"Unexpected {err=}, {type(err)=} in connecting client to address.")
                continue
            else:
                self.logs.insert(0, f"Client on address {addr} successfully connected.")

        self.receiveThread.join()
        self.logs.insert(0, "Server has quit.")

    def handleClients(self):

        while self.running:
            if len(self.socketList) == 0:
                continue

            selectedSockets, _, _ = select.select(self.socketList, [], [], 1)
            self.clientManager.keepAliveCheck()

            if selectedSockets:
                for mySocket in selectedSockets:

                    try:
                        data = readPackage(mySocket)
                    except Exception as e:
                        self.clientManager.clientSocketFailed(mySocket)

                    else:
                        newPackage = Package()
                        newPackage.deserialize(data)

                        self.clientManager.applyPackage(newPackage, mySocket)

    def removeSocketFromList(self, socket):
        self.socketList.remove(socket)

    def serverISKill(self):
        self.serverSocket.close()

        for socket in self.socketList:
            socket.close()

        self.running = False
