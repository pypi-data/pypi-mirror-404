# 导入模块
import requests
from myClass.myRandomUserAgent import random_ua
from lxml import etree
import time
import random
from myClass.chaojiying import Chaojiying_Client
import hashlib


class MyRequests():
    def __init__(self):
        # 创造请求头
        self.headers = {'User-Agent': random_ua()}  # 随机头
        print('爬虫已开启')

    # get请求获取html数据
    def get_html(self, url, headers=None):
        if headers:
            response = requests.get(url, headers=headers)
        else:
            response = requests.get(url, headers=self.headers)
        response.encoding = "utf-8"
        html = response.text
        cookies = response.cookies
        cookies = ';'.join(['{}={}'.format(item[0], item[1]) for item in cookies.items()])  # 格式化为字符串
        return html, cookies, self.headers

    def post_json(self, url, headers=None, form_data=None, cookies=None, json=None):  # form_data是字典格式
        if headers:
            response = requests.post(url, data=form_data, headers=headers, cookies=cookies, json=json)  # 传json就不传form_data,json='{"start":0,"limit":7,"TYPE@=":"2","OPEN@=":"1"}'，F12中点view source即可获得
        else:
            response = requests.post(url, data=form_data, headers=self.headers, cookies=cookies, json=json)  # 传json就不传form_data,json='{"start":0,"limit":7,"TYPE@=":"2","OPEN@=":"1"}'，F12中点view source即可获得
        json_ = response.json()
        return json_

    def myPost(self, url, form_data, cookies=None):
        response = requests.post(url, data=form_data, headers=self.headers, cookies=cookies)
        print(requests)
        print(response.text)
        print(response.content)
        # content = json.loads(response.text)
        # print(content)
        # result = content['data'][0]['v']  # 获取翻译结果
        # return result

    # 通过xpath定位，获取图片的url
    def use_xpath_get_list(self, html, pic_xpath):
        tree = etree.HTML(html)
        picture_list = tree.xpath(pic_xpath)
        return picture_list

    # 检测是否重复爬取url
    def duplicate_img_url(self, url):
        with open('down_img_url.txt', 'r', encoding='utf-8') as f:
            img_url_list = f.read().split('\n')
        if url in img_url_list:
            print('重复图片，决绝下载')
            return '重复'
        else:
            with open('down_img_url.txt', 'a', encoding='utf-8') as f:
                f.write(url + '\n')
            random_time = random.random()*50
            print('等待{}s'.format(random_time))
            time.sleep(random_time)
            return '不重复'

    # 通过图片的url下载图片
    def down_img_wx(self, jpg_url, path='.'):
        is_going_on = self.duplicate_img_url(jpg_url)
        if is_going_on == "不重复":
            response = requests.get(jpg_url, headers=self.header)
            time.sleep(random.randint(0, 10))
            fileName = str(int(time.time()))+''.join(random.sample(['0','1','2','3','4','5','6','7','8','9'], 8))  # 构建不重复的16位文件名
            with open('{}\{}.jpg'.format(path, fileName), 'wb') as f:
                f.write(response.content)
            print('一张图片已经完成下载')
            return response

    def down_img_yx(self, path, jpg_url, fileName):
        is_going_on = self.duplicate_img_url(jpg_url)
        if is_going_on == "不重复":
            response = requests.get(jpg_url, headers=self.header)
            with open('{}\{}.jpg'.format(path, fileName), 'wb') as f:
                f.write(response.content)
            print('一张图片已经完成下载')
            return response

    # 写入第一次获取的html，用于检测是否获取到指定元素
    def write_test_html(self, html):
        with open('1.html', 'w', encoding='utf-8') as f:
            f.write(html)

    # 读取测试的html文件
    def read_test_html(self, ):
        with open('1.html', 'r', encoding='utf-8') as f:
            return f.read()

    # 读取文本类型的url
    def read_txt_pic_url(self, txtPath):
        with open(txtPath, 'r', encoding='utf8') as f:
            return f.read().split('\n')

    def foodiesfeed(self):
        # foodiesfeed爬取
        url = 'https://www.foodiesfeed.com/'
        pic_xpath = '//picture/img/@src'
        html = self.get_html(url)
        picture_list = self.get_jpg_url(html, pic_xpath)
        n = 0
        for pic in picture_list:
            n += 1
            self.down_img(pic)
            time.sleep(random.randint(10))

    def get_timesimp(self):
        # 13位时间戳
        return str(int(time.time()*1000))

    def imgValidCode_cookies(self, img_url):
        print('获取图片验证码和cookies')
        respones = self.down_img_wx(img_url)  # 获取图片的二进制码
        chaojiying = Chaojiying_Client('kkbkkb', 'kkb123456', '	919769')  # 用户中心>>软件ID 生成一个替换 96001
        # im = open('a.jpg', 'rb').read()  # 本地图片文件路径 来替换 a.jpg 有时WIN系统须要//
        imgValidCode = chaojiying.PostPic(respones.content, 1902)['pic_str']
        print('验证码：'+imgValidCode)
        cookies = respones.cookies.get_dict()
        return (imgValidCode, cookies) # 返回验证码和cookies的字典

    def zxyh(self):
        '''
        中信银行模拟登录
        url = 'https://uc.creditcard.ecitic.com/citiccard/ucweb/toRegister.do?sid=ECCQDS047&renqun_youhua=1797112&bd_vid=11551919562866456852'
        '''

        '''
        第一步：给验证码接口发送请求，获取新的验证码
        思考：如何获取到图片验证码接口,以及该url的规律，请求方式是什么，需要携带哪些数据，返回的数据是什么？
            对比刷新前和刷新后url的变化寻找规律
        '''
        img_url = 'https://uc.creditcard.ecitic.com/citiccard/ucweb/newvalicode.do?time=' + self.get_timesimp()
        imgValidCode, cookies = self.imgValidCode_cookies(img_url)  # 获取验证码和cookies
        time.sleep(3)

        '''
        第二步：给短信接口发送请求，获取新的短信验证码
        思考：如何获取短信验证码接口，以及该url的规律，请求方式是什么，需要携带哪些数据，返回的数据是什么？
        '''
        short_message_url = 'https://uc.creditcard.ecitic.com/citiccard/ucweb/getsms.do?&timestamp=' + self.get_timesimp()
        form_data1 = {
            'phone': 18086829907,
            'imgValidCode': imgValidCode
        }
        short_message = self.myPost(url=short_message_url, form_data=form_data1, cookies=cookies)  # 给短信接口发送请求
        print(short_message)  # 验证是否有收到短信发送成功
        time.sleep(3)

        '''
        第三步：点击下一步进行注册
        思考：如果获取下一步按钮对应的接口，该url的规律，请求方式是什么，需要携带哪些数据,返回的数据是什么？
            抓包接口时，页面如果有跳转，则chrome自带的抓包工具会自动刷新，只能抓到跳转后，新页面的一些内容，无法抓到数据提交到的接口
            使用charles抓包，找到contents中有电话和验证码的url
        '''
        smsCode = input('请输入短信验证码：')
        next_url = 'https://uc.creditcard.ecitic.com/citiccard/ucweb/registrycheck.do?&timestamp=' + self.get_timesimp()
        form_data2 = {
            'phone': 18086829907,
            'smsCode': smsCode
        }
        res_json = self.myPost(next_url, form_data2, cookies=cookies)
        print(res_json)  # 获得查询成功则表示成功

        '''
        第四步：输入密码，发送给注册的接口
        思考：如果获取下一步按钮对应的接口，该url的规律，请求方式是什么，需要携带哪些数据,返回的数据是什么？
        
        '''
        password_url = 'https://uc.creditcard.ecitic.com/citiccard/ucweb/register.do?&timestamp=' + self.get_timesimp()
        pass_word = input('输入密码：')
        MD5 = hashlib.md5(bytes(pass_word, encoding='utf8')).hexdigest()
        form_data3 = {
            'Name':'Value',
            'password':MD5
        }
        json_ = self.myPost(password_url, form_data3, cookies=cookies)
        print(json_)

if __name__ == "__main__":
    myRequests = MyRequests()
    myRequests.zxyh()

