from multiprocessing import Process
import os, time
'''
多进程的类，在主进程中调用这个类，就能启动一个拥有以下方法的进程。如果需要开启不同方法的进程，只需在创建一个这个类，重写一个方法来调用即可
'''
class MyProcess(Process):
    def __init__(self, name):
        Process.__init__(self) #调用此类时，实例化对象就有了Process的属性
        self.name = name #调用此类时，实例化对象就有了name的属性

    #二次封装后的类可以将子进程要执行的函数也封装在自己的进程类里面
    def testProcess(self):
        print('子进程{}启动，ID号：{}'.format(self.name, os.getpid()))
        #子进程的功能就能写在中间
        time.sleep(3)
        print('子进程{}结束，ID号：{}'.format(self.name, os.getpid()))