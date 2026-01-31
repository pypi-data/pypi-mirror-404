from redis import ConnectionPool, Redis


class Operating_Redis():
    def __init__(self, host='127.0.0.1', port='6379', db=0, password='135cylpsx'):
        # 建立连接池
        redis_pool = ConnectionPool(host=host, port=port, password=password, db=db, decode_responses=True)
        # 每个连接都使用同一个连接池，避免多次创建连接，断开连接，造成资源浪费
        self.redis_conn = Redis(connection_pool=redis_pool)

    def set(self, key, value, ex=None, px=None, nx=False, xx=False):
        '''
        设置单个值
        :param key: 键
        :param value: 值
        :param ex: 过期时间（秒），时间到了后redis会自动删除
        :param px: 过期时间（毫秒），时间到了后redis会自动删除。ex、px二选一即可
        :param nx: 如果设置为True，则只有name不存在时，当前set操作才执行
        :param xx: 如果设置为True，则只有name存在时，当前set操作才执行
        :return: None
        '''
        self.redis_conn.set(key, value, px=px, nx=nx, xx=xx)

    def get(self, key):
        '''
        获取单个值
        :param key: 键
        :return: str
        '''
        return self.redis_conn.get(key)

    def mset(self, dic):
        '''
        设置多个值
        :param dic: {'key1':'value1','key2':'value2'}
        :return: None
        '''
        self.redis_conn.mset(dic)

    def mget(self, keyList):
        '''
        获取多个值
        :param keyList: ['key1','key2']
        :return: list[str]
        '''
        return self.redis_conn.mget(keyList)

    def getset(self, key, value):
        '''
        给已有的key更新value
        :param key: 键
        :param value: 值
        :return: None
        '''
        self.redis_conn.getset(key, value)

    def setrange(self, key, offset, value):
        '''
        根据索引修改某个键的value值
        :param key: 键
        :param offset: 索引，从0开始
        :param value: 值
        :return: int，该字符串的长度
        '''
        length = self.redis_conn.setrange(key, offset, value)
        return length

    def getrange(self, key, start, end):
        '''
        根据索引获取某个键的部分value
        :param key: 键
        :param start: 起始值，0
        :param end: 结束值，2
        :return: str，截取的字符串，如果所给的键不存在，则返回二进制空值：b''
        '''
        return self.redis_conn.getrange(key, start, end)

    def strlen(self, key):
        '''
        获取value的长度
        :param key: 键
        :return: int，value的长度
        '''
        return self.redis_conn.strlen(key)

    def incr(self, key, amount=1):
        '''
        int类型的value自增
        :param key: 键
        :param amount: 自增量
        :return: int，修改后的值
        '''
        return self.redis_conn.incr(key, amount)

    def decr(self, key, amount=1):
        '''
        int类型的value自减
        :param key: 键
        :param amount: 自增减
        :return: int，修改后的值
        '''
        return self.redis_conn.decr(key, amount)

    def incrbyfloat(self, key, amount=1.0):
        '''
        float类型的value自增
        :param key: 键
        :param amount: 自增量
        :return: float，修改后的值
        '''
        return self.redis_conn.incrbyfloat(key, amount)

    def append(self, key, value):
        '''
        value后面追加str
        :param key: 键
        :param value: 值
        :return: int，修改后value的长度
        '''
        return self.redis_conn.append(key, value)

    def lpush(self, key, *args):
        '''
        从列表的左侧添加值，多个value时，从左到右依次添加到列表的左侧，类型可以不同，
        ['a'].lpush('a',1,2,3), [3,2,1,'a']
        所给的key不存在，则新建一个列表
        :param key: 键
        :param args: *values
        :return: int，列表的长度
        '''
        return self.redis_conn.lpush(key, *args)

    def rpush(self, key, *args):
        '''
        从列表的右侧添加值，多个value时，从左到右依次添加到列表的右侧，类型可以不同
        ['a'].lpush('a',1,2,3), ['a',1,2,3]
        所给的key不存在，则新建一个列表
        :param key: 键
        :param args: *values
        :return: int，列表的长度
        '''
        return self.redis_conn.rpush(key, *args)

    def lpushx(self, key, *args):
        '''
        只有键存在时，才添加。若键不存在则不添加，也不新创建列表
        从列表的左侧添加值，多个value时，从左到右依次添加到列表的左侧，类型可以不同，
        ['a'].lpush('a',1,2,3), [3,2,1,'a']
        所给的key不存在，则新建一个列表
        :param key: 键
        :param args: *values
        :return: int，列表的长度
        '''
        return self.redis_conn.lpush(key, *args)

    def rpushx(self, key, *args):
        '''
        只有键存在时，才添加。若键不存在则不添加，也不新创建列表
        从列表的右侧添加值，多个value时，从左到右依次添加到列表的右侧，类型可以不同
        ['a'].lpush('a',1,2,3), ['a',1,2,3]
        所给的key不存在，则新建一个列表
        :param key: 键
        :param args: *values
        :return: int，列表的长度
        '''
        return self.redis_conn.rpush(key, *args)

    def llen(self, key):
        '''
        获取所给键的列表大小
        :param key: 键
        :return: int，len(list)
        '''
        return self.redis_conn.llen(key)

    def linsert(self, key, where, refvalue, value):
        '''
        在列表中间插入新值
        :param key: 键
        :param where: 'before' or 'after', 在某值的前面或后面添加
        :param refvalue: 指定某个值的前后插入
        :param value: 插入的新值
        :return: int，插入后列表的长度，如果refvalue不存在，则返回-1
        '''
        return self.redis_conn.linsert(key, where, refvalue, value)

    def lset(self, key, index, value):
        '''
        列表中通过索引赋值
        :param key: 键
        :param index: 索引
        :param value: 值
        :return: boolean，成功Ture，否则False
        '''
        return self.redis_conn.lset(key, index, value)

    def lindex(self, key, index):
        '''
        通过索引获取列表的值
        :param key: 键
        :param index: 索引
        :return: value
        '''
        return self.redis_conn.lindex(key, index)

    def lrange(self, key, start, end):
        '''
        列表中获取一段数据
        :param key: 键
        :param start: 起始值0
        :param end: 结束值
        :return: list
        '''
        return self.redis_conn.lrange(key, start, end)

    def lpop(self, key):
        '''
        删除左边第一个值
        :param key:
        :return: 被删除的元素
        '''
        return self.redis_conn.lpop(key)

    def rpop(self, key):
        '''
        删除右边第一个值
        :param key:
        :return: 被删除的元素
        '''
        return self.redis_conn.rpop(key)

    def lrem(self, key, count, value):
        '''
        删除列表中N个相同的值
        :param key: 键
        :param count: 删除的个数，正整数表示从左往右，负整数表示从右往左，例如：2，-2
        :param value: 需要删除的值
        :return: int，返回删除的个数
        '''
        return self.redis_conn.lrem(key, count, value)

    def ltrim(self, key, start, end):
        '''
        删除列表中范围之外的所有值
        :param key: 键
        :param start: 起始值
        :param end: 结束值
        :return: boolean，成功True，否则False
        '''
        return self.redis_conn.ltrim(key, start, end)

    def rpoplpush(self, srclist, dstlist):
        '''
        一个列表中最右边值取出后添加到另一个列表的最左边
        :param srclist: source，源列表
        :param dstlist: destination，目标列表
        :return: 取出的元素
        '''
        return self.redis_conn.rpoplpush(srclist, dstlist)

    def hset(self, name, key, value):
        '''
        哈希集中添加一对键值对，
        数据格式为name:[{key,value}]
        :param name: 哈希集名字
        :param key: 键
        :param value: 值
        :param px: 过期时间（毫秒），时间到了后redis会自动删除。ex、px二选一即可
        :param nx: 如果设置为True，则只有name不存在时，当前set操作才执行
        :param xx: 如果设置为True，则只有name存在时，当前set操作才执行
        :return: int，返回添加成功的个数
        '''
        return self.redis_conn.hset(name, key, value)

    def hmset(self, name, mapping):
        '''
        设置哈希中的多个键值对
        :param name: 名
        :param mapping: dict字典
        :return: 成功True
        '''
        return self.redis_conn.hmset(name, mapping)

    def hmget(self, name, keys):
        '''
        获取哈希中多个键值对
        :param name: 名
        :param keys: [key1, key2]
        :return: list, [value1, value2]
        '''
        return self.redis_conn.hmget(name, keys)

    def hget(self, name, key):
        '''
        获取哈希中多个键值对
        :param name: 名
        :param keys: key1
        :return: 元素, value1
        '''
        return self.redis_conn.hget(name, key)

    def hgetall(self, key):
        '''
        获取哈希中多个键值对
        :param name: 名
        :param keys: key1
        :return: 元素, value1
        '''
        return self.redis_conn.hgetall(key)


    def delAll(self):
        return self.redis_conn.flushdb()

    def delete(self, key):
        '''
        删除string类型数据
        :param key: string
        '''
        return self.redis_conn.delete(key)

    def keys(self, keys):
        '''
        获取key
        :param keys: 'key1 key2'  or  '*' 
        :return: ['key1', 'key2']
        '''
        return self.redis_conn.keys(keys)
        
if __name__ == '__main__':
    # 应用场景：缓存 队列任务 应用排行榜 网站访问统计 数据过期处理 分布式集群架构中的session分离
    operating_redis = Operating_Redis()
    operating_redis.set('a', 'b', px=3000)  # 设置键值对，并在3秒后过期
    print(operating_redis.get('a'))  # 'b'，获取键为'a'的值
    operating_redis.mset({'x':'abc', 'y':'bcd', 'z':'cde'})  # 设置多个键值对
    print(operating_redis.mget(['x', 'y', 'z']))  # ['abc','bcd','cde']，获取多个键值对
    operating_redis.getset('x', 5)  # 更新'x'键的值
    print(operating_redis.setrange('y', 1, 'a'))  # 3，更新'y'键某个索引位置的值，返回该字符串的长度
    print(operating_redis.getrange('z', 0, 1))  # cd， 获取'z'键的切片数据
    print(operating_redis.strlen('x'))  # 1，返回'x'键的value的长度
    print(operating_redis.incr('x')) # 6，'x'键，自增1
    print(operating_redis.incr('x', 2)) # 8，'x'键，自增1
    print(operating_redis.decr('x')) # 7，'x'键，自减少1
    print(operating_redis.decr('x', 2)) # 5，'x'键，自减少1
    print(operating_redis.incrbyfloat('x')) # 6.0，'x'键，自增1.0
    print(operating_redis.incrbyfloat('x', 2.0)) # 8.0，'x'键，自增2.0
    print(operating_redis.append('y', 'bcd')) # 6，len('badbcd')，'y'键的value后面追加'bcd'
    print(operating_redis.lpush('lis1', '1', '2')) # 2，len(['2', '1'])，返回列表长度，左侧添加元素
    print(operating_redis.rpush('lis2', '1', '2')) # 2，len(['1', '2'])，返回列表长度，右侧添加元素
    print(operating_redis.lpushx('lis1', '1', '2'))  # 2，len(['2', '1'])，返回列表长度，只有key存在时，左侧添加元素，不存在也不创建
    print(operating_redis.rpushx('lis2', '1', '2'))  # 2，len(['1', '2'])，返回列表长度，只有key存在时，右侧添加元素，不存在也不创建
    print(operating_redis.llen('lis1'))  # 8，返回列表长度
    print(operating_redis.linsert('lis1', 'after', '2', 'a'))  # 3，在'2'的后面添加'a'，如果'lis1'中有多个'2'，只在第一个'2'后添加元素
    print(operating_redis.lset('lis2', 2, 'cc'))  # True，在索引2的位置添加'cc'
    print(operating_redis.lindex('lis2', 2))  # 'cc'，获取索引2位置的元素
    print(operating_redis.lrange('lis2', 0, -1))  # ['',''...]，获取列表中的元素
    print(operating_redis.lpop('lis1'))  # 元素，删除列表左边第一个元素，并返回该元素
    print(operating_redis.rpop('lis1'))  # 元素，删除列表右边第一个元素，并返回该元素
    print(operating_redis.lrem('lis1', 5, '1'))  # 5，成功删除元素的个数，从左往右删除5个'1'
    print(operating_redis.lrem('lis1', -5, '1'))  # 5，成功删除元素的个数，从右往左删除5个'1'
    print(operating_redis.ltrim('lis1', 0, 2))  # True，删除[0,2]范围之外的所有值
    print(operating_redis.ltrim('lis2', 0, 2))  # True，删除[0,2]范围之外的所有值
    print(operating_redis.rpoplpush('lis1', 'lis2'))  # 'a'，返回移动的元素，lis1最右边的值添加到lis2的最左边
    print(operating_redis.hset('hash1', 'a', 'b'))  # 1，返回成功添加的个数，在哈希集'hash1'中添加{'a':'b'}
    print(operating_redis.hmset('hash2', {'a':'1', 'b':'2'}))  # True，哈希集'hash2'中添加{'a':'1', 'b':'2', 'c':'3'}
    print(operating_redis.hmget('hash2', ['a', 'b']))  # ['1','2']，获取哈希集hash2中的多个值
    print(operating_redis.hget('hash1', 'a'))  # 'b'，获取哈希集hash1中的一个值
    operating_redis.delAll()