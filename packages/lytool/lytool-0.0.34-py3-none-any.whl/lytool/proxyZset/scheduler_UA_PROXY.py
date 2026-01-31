TESTER_CYCLE = 20
GETTER_CYCLE = 20
TESTER_ENABLED = True    #开关测试ip模块
GETTER_ENABLED = False    #开关爬取ip模块
API_ENABLED = True       #开关api接口模块
API_HOST = 'localhost'
API_PORT = '5555'
PROXY_POOL_URL = 'http://localhost:5555/random'

from multiprocessing import Process
from apiProxy import app
from getProxy import Getter
from testProxy import Tester
from save_Get_UA_Proxy import RedisClient
import requests
import time
from random import choice

class Scheduler():
    def schedule_tester(self, cycle=TESTER_CYCLE):
        tester = Tester()
        while True:
            print('测试器开始运行')
            tester.run()
            time.sleep(cycle)

    def schedule_getter(self, cycle=GETTER_CYCLE):
        getter = Getter()
        while True:
            print('开始抓取代理')
            getter.run()
            time.sleep(cycle)

    def schedule_api(self):
        #开启API
        print('接口开启')
        app.run(API_HOST, API_PORT)

    def run(self):
        print('代理池开始运行')
        if TESTER_ENABLED:    #测试代理池
            tester_process = Process(target=self.schedule_tester)
            tester_process.start()

        if GETTER_ENABLED:    #获取代理池
            getter_process = Process(target=self.schedule_getter)
            getter_process.start()

        if API_ENABLED:    #代理池接口
            api_process = Process(target=self.schedule_api)
            api_process.start()

    #从api端口获取一个随机代理
    def get_proxy(self):
        try:
            response = requests.get(PROXY_POOL_URL)
            if response.status_code == 200:
                print('Get Proxe', response.text)
                return response.text
            return None
        except requests.ConnectionError:
            return None

if __name__ == '__main__':
    sch = Scheduler()
    sch.run()
    # sch.get_proxy()
    # sch.get_userAgent()
    # print(sch.get_userAgnetList())
    # print(len(sch.get_proxyList()))
