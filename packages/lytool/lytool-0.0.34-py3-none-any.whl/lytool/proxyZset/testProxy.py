from save_Get_UA_Proxy import RedisClient
import aiohttp
import asyncio
import time
VALID_STATUS_CODES = [200]
TEST_URL = 'https://www.mzitu.com/tag/youhuo/'
BATCH_TEST_SIZE = 100

class Tester(object):
    def __init__(self):
        self.redis = RedisClient()    #链接redis数据库

    #切换代理，测试百度是否能打开
    async def test_single_proxy(self, proxy):
        conn = aiohttp.TCPConnector(ssl=False)
        #异步开启会话
        async with aiohttp.ClientSession(connector=conn) as session:
            try:
                if isinstance(proxy, bytes):    #判断proxy是否为字节类型
                    proxy = proxy.decode('utf-8')    #解码
                real_proxy = 'http://' + proxy    #此变量运用到这里：async with session.get(TEST_URL, proxy=real_proxy, timeout=15) as response:
                print('正在测试', proxy)
                #异步发起请求，超时15报错
                async with session.get(TEST_URL, proxy=real_proxy, timeout=15) as response:
                    if response.status in VALID_STATUS_CODES:
                        self.redis.max(proxy)
                    else:
                        self.redis.decrease(proxy)
            except (aiohttp.ClientError, aiohttp.ClientConnectorError, asyncio.TimeoutError, TimeoutError, AttributeError):
                self.redis.decrease(proxy)
                print('代理请求失败', proxy)

    def run(self):
        print('测试器开始运行')
        try:
            proxies = self.redis.all()
            loop = asyncio.get_event_loop()
            for i in range(0, len(proxies), BATCH_TEST_SIZE):    #range(0, 1000, 100) --> for i in [0,100,200,300,400,500....]
                test_proxies = proxies[i:i + BATCH_TEST_SIZE]    #遍历列表，列表切片,第一次：proxies[0, 100]; 第二次：proxies[100, 200]
                tasks = [self.test_single_proxy(proxy) for proxy in test_proxies]    #test_proxies的最大长度即100
                loop.run_until_complete(asyncio.wait(tasks))
                time.sleep(5)
        except Exception as e:
            print('测试器发生错误', e.args)

if __name__ == '__main__':
    tester = Tester()
    tester.run()