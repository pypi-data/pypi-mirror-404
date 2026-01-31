'''
遇到错误：
fake_useragent.errors.FakeUserAgentError: Maximum amount of retries reached

# 解决办法一：
pip install -U fake-useragent

# 解决方法二
import tempfile
print(tempfile.gettempdir())
https://pan.baidu.com/s/1_Qv1LGBSjO2bnF4ocMqhwQ 提取码: 2hpu
将json文件放到tempfile.gettempdir()中

参考来源：https://blog.csdn.net/xc_zhou/article/details/106412377
'''

from fake_useragent import UserAgent
def random_ua():
    return str(UserAgent().random)

if __name__ == '__main__':
    print(random_ua())
