import urllib.request
import urllib.parse
import json
import time
import pickle
from myClass.headers import Headers
import os
import ssl
from collections import deque
from myClass.regularExpression import RegularExpression
import random
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
from PIL import ImageEnhance

class MySpider(object):
    #得到一个请求头
    def getHeaders(self, **kwargs):
        '''
        :param kwargs: 不同网站需要的头部信息不一定只是User-Agent，需要用fiddler抓包一次，确定其头部信息内容，在用关键字参数的形式添加头部信息内容
        :return: 返回请求头
        '''
        AgentList = [
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60 Opera/8.0 (Windows NT 5.1; U; en)',
            'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
            'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)"',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
            'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0',
            'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5',
            'Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
            'Mozilla/5.0 (Linux; U; Android 2.2.1; zh-cn; HTC_Wildfire_A3333 Build/FRG83D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
            'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10',
            'Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13',
            'Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+',
            'Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0',
            'Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)',
            'UCWEB7.0.2.37/28/999',
            'NOKIA5700/ UCWEB7.0.2.37/28/999',
            'Openwave/ UCWEB7.0.2.37/28/999',
            'Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999'
        ]
        agent = random.choice(AgentList)
        headers = {
            'User-Agent': agent,
        }
        headers.update(kwargs)
        return headers

    #得到一个HtmlBytes
    def getHtmlBytes(self, url):
        headers = self.getHeaders()
        res = urllib.request.Request(url, headers=headers)
        context = ssl._create_unverified_context()  # 解决https安全拦截
        time.sleep(random.randint(10, 30))
        response = urllib.request.urlopen(res, context=context)
        return response.read()

    #HtmlBytes写入.html
    def writeFileHtmlBytes2Html(self, htmlBytes, toPath):
        with open(toPath, 'wb') as f:
            f.write(htmlBytes)

    #HtmlBytes写入.txt
    def writeFileHtmlBytes2Txt(self, htmlBytes, toPath):
        with open(toPath, 'w') as f:
            f.write(str(htmlBytes))

    #中央控制器：队列遍历所有不重复url
    def center(self, url, toPath, tagetCrawler):
        queue = deque()
        queue.append(url)
        while len(queue) != 0:
            targetUrl = queue.popleft()
            time.sleep(20)
            urlList = tagetCrawler(targetUrl, toPath)
            for urlTuple in urlList:
                needUrl = urlTuple[0]
                queue.append(needUrl)

    #url的参数处理
    def getParameter(self, url, word, **kwargs):
        '''
        :param url: 目标网站网址
        :param word: get请求的值
        :param kwargs: 字典，用于将原来网址中的参数值，更新为字典中的键值对
        :return:
        '''
        urlResult = urllib.parse.unquote(url)
        parameter = urlResult.split('?')[1]
        dic = {}
        for item in parameter.split('&'):
            k = item.split('=')[0]
            v = item.split('=')[1]
            if v.isdigit():
                dic[k] = int(v)
                continue
            dic[k] = v
        dic.update(kwargs)
        query_string = urllib.parse.urlencode(dic)
        baseUrl = 'http://www.baidu.com/s?'
        url = baseUrl + query_string
        headers = self.getHeaders()
        request = urllib.request.Request(url=url, headers=headers)
        response = urllib.request.urlopen(request)
        filedName = word + '.html'
        with open(filedName, 'wb') as fp:
            fp.write(response.read())

    def getCrawler(self, urlCope):
        '''
        :param urlCope: 需要访问的网站url，需要观察其发送get请求后，其get值得参数的命名，需要修改wd与之相等
        :return: None
        :调用方式： urlCope = 'https://www.baidu.com/s?wd=%E9%99%88&rsv_spt=1&rsv_iqid=0xb0f99ab9001d0526&issp=1&f=8&rsv_bp=1&rsv_idx=2&ie=utf-8&tn=57028281_hao_pg&rsv_enter=1&rsv_sug3=5&rsv_sug1=4&rsv_sug7=100&rsv_t=c3185SKQWFvBSCJj5sXeRzWpb175%2Fl6wrKBl9KYr3BCiuHZ%2B3V2roSGxKXaQXp2oQ83k%2FioC&rsv_sug2=0&inputT=1977&rsv_sug4=1977&rsv_sug=1'
                  getCrawler(urlCope)
        '''
        word = input('请输入你想查询的内容：')
        urlCope = urlCope
        self.getParameter(urlCope, word, wd=word)

    def postCrawler(self, post_url):
        '''
        :param post_url: ajax接口，查询ajax接口的方式可以通过谷歌浏览器抓包得到
        :return:
        调用方式
            post_url = 'https://fanyi.baidu.com/sug/'
            postCraler(post_url)
        注意：post请求的数据格式必须是b'kw=%E8%8B%B9%E6%9E%9C'
        '''
        word = input('请输入您需要查询的单词：')
        form_data = {'kw': word}  # 构建post表单数据
        form_data = urllib.parse.urlencode(form_data).encode()  # 处理post参数，post请求的数据格式必须是b'kw=%E8%8B%B9%E6%9E%9C'
        headers = self.getHeaders()
        request = urllib.request.Request(url=post_url, headers=headers)
        response = urllib.request.urlopen(request, form_data)
        with open('{}.html'.format(word), 'wb') as fp:
            fp.write(response.read())

    # 保存图片
    def seveImage(self, url, path):
        urllib.request.urlretrieve(url, filename=path)

    # 获取同城帮手机商品信息的字典
    def getInfoDict(self, allCommodity, pictureSavePath):
        commodityInfoList = []
        num = 1
        for i in range(len(allCommodity)):
            picture = allCommodity[i].find('img')['src']
            commodityName = allCommodity[i].find('h3').text
            commodityAttr = allCommodity[i].find('p').text
            price = allCommodity[i].find('div', attrs={'class': 'p-price-cur'}).text
            if allCommodity[i].find('div', attrs={'class': 'p-price-r'}) != None:
                discount = allCommodity[i].find('div', attrs={'class': 'p-price-r'}).text.split(' ')[1]
                originalPrice = allCommodity[i].find('div', attrs={'class': 'p-price-r'}).text.split(' ')[2]
            else:
                discount = None
                originalPrice = None
            advantage = allCommodity[i].find('div', attrs={'class': 'p-desc'}).text
            policy = allCommodity[i].find('i').text
            commodityInfo = {}
            commodityInfo['No.{}'.format(num)] = {'picture': picture,
                                                  'commodityName': commodityName,
                                                  'commodityAttr': commodityAttr,
                                                  'price': price,
                                                  'discount': discount,
                                                  'originalPrice': originalPrice,
                                                  'advantage': advantage,
                                                  'policy': policy
                                                  }
            commodityInfoList.append(commodityInfo)
            # time.sleep(random.randint(10, 20))
            # myCra.seveImage(picture, pictureSavePath.format(num, num))  # 保存图片
            num += 1
        return commodityInfoList

    # 网页数据提取执行主程序
    def getJsonInfo(self, pictureSavePath, jsonSavePath, htmlFilePath, tagName, attribute, attributeValue):
        fileList = os.listdir(htmlFilePath)
        pageInfoList = []
        num = 0
        for i in fileList:
            absPath = os.path.join(htmlFilePath, i)
            with open(absPath, 'rb') as f:
                data = f.read().decode('utf-8')
                soup = BeautifulSoup(data, features='lxml')
                # 找到一页的所有商品信息的div即div[class='class']*20
                allCommodity = soup.find_all(tagName, attrs={attribute: attributeValue})
            #获取每一页的商品信息
            info = self.getInfoDict(allCommodity, pictureSavePath)
            pageInfo = {}
            pageInfo['{}page'.format(num)] = info
            num += 1
            pageInfoList.append(pageInfo)
            # time.sleep(random.randint(20, 30)) #需要将图片保存到本地才取消注释
        jsonFile = json.dumps(pageInfoList)
        with open(jsonSavePath, 'w') as f:
            json.dump(jsonFile, f)

    #同城帮的各种路径
    def cityGang(self):
        # 图片保存地址
        pictureSavePath = r'D:\qian_feng_education\first_project\finishedObject\同城帮数据爬取\image\{}page\{}.jpg'
        # json保存地址
        jsonSavePath = r'D:\qian_feng_education\first_project\finishedObject\同城帮数据爬取\json\同城帮商品数据.json'
        # HTML文件夹路径
        htmlFilePath = r'D:\qian_feng_education\first_project\finishedObject\同城帮数据爬取\htmls'
        return pictureSavePath, jsonSavePath, htmlFilePath

    #图片验证码识别
    def verificationCode(self, path):
        '''
        :param path:图片路径
        :return: 已经识别的字符串
        '''
        img = Image.open(path)
        # 图片数据预处理
        # 图片数据预处理第一步
        img = img.convert('RGB')
        enhancer = ImageEnhance.Color(img)
        enhancer = enhancer.enhance(0)
        enhancer = ImageEnhance.Brightness(enhancer)
        enhancer = enhancer.enhance(2)
        enhancer = ImageEnhance.Contrast(enhancer)
        enhancer = enhancer.enhance(8)
        enhancer = ImageEnhance.Sharpness(enhancer)
        enhancer = enhancer.enhance(20)

        # 图片数据预处理第二步——灰度处理
        img = img.convert('L')
        # img.show()
        # 图片数据预处理第三步——二值化处理
        threshold = 140
        table = []
        for i in range(256):
            if i < threshold:
                table.append(0)
            else:
                table.append(1)
        out = img.point(table, '1')
        out.show()
        # 学习验证码图片
        return pytesseract.image_to_string(img)

if __name__ == '__main__':
    # 实例化爬虫
    myCra = MySpider()
    path = myCra.cityGang()
    myCra.getJsonInfo(path[0], path[1], path[2], 'div', 'class', 'p-item') #图片保存地址，json保存地址，HTML文件夹路径，一个页面中的一个商品的div或其他tagName，这个div的属性名，这个div的属性值