import socket
import threading
class MyClient(object):
    def __init__(self, ip, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip, port))

    def connectServer(self):
        while True:
            info = self.client.recv(1024).decode('utf-8')


    def connectThreading(self):
        t = threading.Thread(target=self.connectServer)
        t.start()

    def sendRegister(self, userName, passWord):
        data = userName + ',' + passWord + ',' + 'register'
        self.client.send(data.encode('utf-8'))

    def sendSignIn(self, userName, passWord):
        data = userName + ',' + passWord + ',' + 'signIn'
        self.client.send(data.encode('utf-8'))