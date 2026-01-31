# 存储模块
MAX_SCORE = 100
MIN_SCORE = 0
INITIAL_SCORE = 10
REDIS_HOST = '192.168.0.104'
REDIS_PORT = 6379
REDIS_PASSWORD = '135cylpsx4848@'
PROXY_KEY = 'proxyKey'
USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60 Opera/8.0 (Windows NT 5.1; U; en)',
  'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
  'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
  'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
  'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER',
  'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36',
  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36',
]


import redis    #导入redis
from  random import choice    #导入随机选择方法

#定义错误类型
class PoolEmptyError(BaseException):
    pass

class RedisClient(object):    #定义一个redis客户端类
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD):
        #链接redis数据库
        self.db = redis.StrictRedis(host=host, port=port, password=password, decode_responses=True)    #decode_responses返回已经解码的数据

    #给数据库增加一个代理
    def add(self, proxy, score=INITIAL_SCORE):
        if not self.db.zscore(PROXY_KEY, proxy):    #先从数据库中查询是否有PROXY_KEY的proxy的值，如果值不存在返回0，0被not后执行if语句，即值不存在才添加该值
            return self.db.zadd(PROXY_KEY, {proxy: score})    #插入一条key为PROXY_KEY,分数为score,value为proxy的有序集合到redis中

    #随机从有序集合中取出代理信息
    def random(self):
        result = self.db.zrangebyscore(PROXY_KEY, MAX_SCORE, MAX_SCORE)    #获取得分为100的数据列表
        if len(result):    #这列表中有值
            return choice(result)    #则随机选择一个代理返回
        else:    #列表中不存在值
            result = self.db.zrevrange(PROXY_KEY, 0, 100)    #在索引0-100的范围取值,并返回列表
            if len(result):    #这个列表中存在值
                return choice(result)    #随机选择一个代理返回
            else:    #列表中不存在值
                raise PoolEmptyError('redis数据库中没有代理')    #抛出Empty的错误异常

    #较少分数
    def decrease(self, proxy):
        score = self.db.zscore(PROXY_KEY, proxy)    #在redis中去获取指定键值的得分，
        if score and score > MIN_SCORE:    #得分存在且大于0
            print('代理:', proxy, '当前得分', score, '减1')
            return self.db.zincrby(PROXY_KEY, -1, proxy)    #将指定键值的得分键一
        else:    #得分为0
            print('代理:', proxy, '当前得分', score, '移除')
            return self.db.zrem(PROXY_KEY, proxy)    #删除指定键值

    #判断是否存在
    def exists(self, proxy):
        return not self.db.zscore(PROXY_KEY, proxy)  == None    #存在返回True，不存在返回False

    #将代理设为最大值
    def max(self, proxy):
        print('代理:', proxy, '可用，设置为', MAX_SCORE)
        return self.db.zadd(PROXY_KEY, {proxy: MAX_SCORE})

    #获取数量
    def count(self):
        return self.db.zcard(PROXY_KEY)    #返回指定key的有序集合中的元素个数

    #获取全部代理
    def all(self):
        return self.db.zrangebyscore(PROXY_KEY, MIN_SCORE, MAX_SCORE)    #返回分数在0-100内的所有value

    #返回USER_AGENTS列表
    def get_userAgentList(self):
        return USER_AGENTS
    
    #获取得分为100的代理列表
    def get_proxyList_redis(self):
        return self.db.zrangebyscore(PROXY_KEY, MAX_SCORE, MAX_SCORE)
    


if __name__ == '__main__':
    testRC = RedisClient()
    # testRC.add('http://123.145.1.1:8010')
    # testRC.add('http://123.145.1.1:8020')
    # testRC.add('http://123.145.1.1:8030')
    # testRC.add('http://123.145.1.1:8040')    #增加代理
    # print(testRC.random())
    # for i in range(11):
    #     testRC.decrease('http://123.145.1.1:8020')    #已经被删除
    # print(testRC.exists('http://123.145.1.1:8010'))    #不存在False
    # print(testRC.exists('http://123.145.1.1:8020'))    #存在True
    # testRC.max('http://123.145.1.1:8020')
    # print(testRC.count())    #返回proxyKey中所有的代理个数
    # print(testRC.all())    #返回列表，元素为代理