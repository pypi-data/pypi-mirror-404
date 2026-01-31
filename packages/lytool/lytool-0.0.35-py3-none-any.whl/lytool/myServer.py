import socket
import threading
import queue
from myClass.myRedis import MyRedis
from myClass.mySql import MySql

class MyServer(object):
    def __init__(self, ip, port, listen):
        self.q = queue.Queue()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((ip, port))
        self.server.listen(listen)
        print('服务器已启动...\n')
        self.redis = MyRedis('135cylpsx4848@')
        self.mysql = MySql('172.20.10.2', 'root', '135cylpsx4848@', 'website')

    #从mysql里查用户名和密码
    def checkUserNamePassWordFromMySQL(self, userName, passWord):
        regisInfo = self.mysql.get_one("select * from registerinfo where userName={}".format(userName))
        if regisInfo == None:
            info = '该用户未注册\n'
            self.resultSaveToRedisAndSend(info)
        elif regisInfo[2] == passWord:
            userName = regisInfo[1]
            passWord = regisInfo[2]
            self.reginsterInfoSaveToRedis(userName, passWord)
            info = '登录成功\n'
            self.resultSaveToRedisAndSend(info)
        elif regisInfo[2] != passWord:
            info = '密码错误\n'
            self.resultSaveToRedisAndSend(info)

    #从redis里查用户名密码
    def checkUserNamePassWordFromRedis(self, userName, passWord):
        if self.redis.get(userName) == passWord:
            info = '登录成功\n'
            self.resultSaveToRedisAndSend(info)
        elif self.redis.get(userName) != False and self.redis.get(userName) != passWord:
            info = '密码错误\n'
            self.resultSaveToRedisAndSend(info)
        elif not self.redis.get(userName):
            self.checkUserNamePassWordFromMySQL(userName, passWord)

    #结果保存到redis并发送
    def resultSaveToRedisAndSend(self, result):
        self.clientSocket.send(result.encode('utf-8'))
        self.redis.set('result', result)

    #注册信息保存到mysql
    def registerInfoSaveToMySQL(self, userName, passWord):
        self.mysql.insert("insert into registerinfo values(0, {}, {});".format(userName, passWord))

    #注册信息保存到redis
    def reginsterInfoSaveToRedis(self, userName, passWord):
        self.redis.set(userName, passWord)

    #保存用户名和密码
    def saveUserNamePassWord(self, userName, passWord):
        result = '用户{}注册成功\n'.format(userName)
        self.resultSaveToRedisAndSend(result)
        self.reginsterInfoSaveToRedis(userName, passWord)
        self.registerInfoSaveToMySQL(userName, passWord)

    #注册或登录
    def registerOrsignIn(self):
        while True:
            data = self.clientSocket.recv(1024).decode('utf-8')
            print('接收到{}客户端发来的信息：{}\n'.format(self.clientAddrees, data))
            userName = data.split(',')[0]
            passWord = data.split(',')[1]
            operation = data.split(',')[2]
            if operation == 'register':
                self.saveUserNamePassWord(userName, passWord)
            elif operation == 'signIn':
                self.checkUserNamePassWordFromRedis(userName, passWord)

    #连接
    def connect(self):
        while True:
            self.clientSocket, self.clientAddrees = self.server.accept()
            print('{}链接服务器\n'.format(self.clientAddrees))
            t = threading.Thread(target=self.registerOrsignIn)
            t.start()

    #连接的线程
    def connectThreadting(self):
        t = threading.Thread(target=self.connect)
        t.start()









