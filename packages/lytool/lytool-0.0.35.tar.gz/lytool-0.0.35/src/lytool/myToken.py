import hashlib
import time
import requests
import json
import random

def api_secret_random():
    lis = ['dsfasdfadsa', 'asdfasdfasdf', 'asdfasdfgfdfdgh']
    return random.choice(lis)

# 创建获取token的对象
class Token(object):
    def __init__(self, api_secret, project_code, account):
        self._API_SECRET = api_secret  #
        self.project_code = project_code
        self.account = account

    def get_token(self):
        timeStamp = int(str(time.time()).replace('.','')[0:13])
        strs = self.project_code + self.account + str(timeStamp) + self._API_SECRET
        hl = hashlib.md5()
        hl.update(strs.encode("utf8"))  # 指定编码格式，否则会报错
        token = hl.hexdigest()
        # print('MD5加密前为 ：', strs)
        # print('MD5加密后为 ：', token)
        return token, timeStamp


if __name__ == '__main__':
    # tokenprogramer = Token('api_secret具体值', 'project_code具体值', 'account具体值')  # 对象实例化
    tokenprogramer = Token(api_secret_random(), 'college', '18086829907')  # 对象实例化
    token, timeStamp = tokenprogramer.get_token()  # 调用token对象
    print(token, timeStamp)