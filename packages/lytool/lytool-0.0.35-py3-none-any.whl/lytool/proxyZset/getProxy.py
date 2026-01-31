import json
from pyquery import PyQuery as pq
import requests
from save_Get_UA_Proxy import RedisClient
import time
from lxml import etree

#爬虫类方法扩展机制
class ProxyMetaClass(type):
    def __new__(cls, name, bases, attrs):
        count = 0
        attrs['__CrawlFunc__'] = []
        for k,v in attrs.items():
            if 'crawl_' in k:
                attrs['__CrawlFunc__'].append(k)
                count += 1
        attrs['__CrawlFuncCount__'] = count
        return type.__new__(cls, name, bases, attrs)

#爬虫类
class Crawler(metaclass=ProxyMetaClass):
    #爬取代理网页
    def get_page(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',}
        return requests.get(url, headers=headers).text
    #调用爬取代理函数
    def get_proxies(self, crawlFuncName):
        proxiesList = []
        for proxy in eval('self.{}()'.format(crawlFuncName)):    #eval函数：将最外层的''去掉，这里是将'self.crawl_xiguadaili()'的引号去掉，让其中的函数表达式进行函数调用
            print('成功获取到代理', proxy)
            proxiesList.append(proxy)
        return proxiesList

    # def crawl_daili66(self, page_count=4):
    #     start_url = 'http://www.66ip.cn/{}.html'
    #     urls = [start_url.format(page) for page in range(1, page_count + 1)]
    #     for url in urls:
    #         print('Crawling:',url)
    #         html = self.get_page(url)
    #         if html:
    #             doc = pq(html)
    #             trs = doc('.containerbox table tr:gt(0)').items()
    #             for tr in trs:
    #                 ip = tr.find('td:nth-child(1)').text()
    #                 port = tr.find('td:nth-child(2)').text()
    #                 yield ':'.join([ip, port])
    #
    # def crawl_proxy360(self):
    #     start_url = 'http://www.proxy360.cn/Region/China'
    #     print('Crawling', start_url)
    #     html = self.get_page(start_url)
    #     if html:
    #         doc = pq(html)
    #         lines = doc('div[name="list_proxy_ip"]').items()
    #         for line in lines:
    #             ip = line.find('.tbBottomLine:nth-child(1)').text()
    #             port = line.find('.tbBottomLine:nth-child(2)').text()
    #             yield ':'.join([ip, port])
    #
    # def crawl_goubanjia(self):
    #     start_url = 'http://www.goubanjia.com/free/gngn/index.shtml'
    #     html = self.get_page(start_url)
    #     if html:
    #         doc = pq(html)
    #         tds = doc('td .ip').items()
    #         for td in tds:
    #             td.find('p').remove()
    #             yield td.text().replace(' ','')

    def crawl_xici(self):
        start_url = 'https://www.xicidaili.com/nn/'
        ipText = self.get_page(start_url)
        item = etree.HTML(ipText)
        itemList = item.xpath('//table[@id="ip_list"]//tr')[1:-1]
        for i in itemList:
            ip = i.xpath('./td[2]/text()')[0]
            port = i.xpath('./td[3]/text()')[0]
            # type = i.xpath('./td[6]/text()')[0]
            # proxy = type.lower() + '://' + ip + ':' + port
            proxy = ip + ':' + port
            yield proxy

    # def crawl_xiguadaili(self):
    #     start_url = 'http://api3.xiguadaili.com/ip/?tid=556587801095918&num=1000'
    #     proxyList = self.get_page(start_url).split('\r\n')  #['93.152.176.249:61384', '58.27.222.130:8080',...]
    #     if len(proxyList) > 0:
    #         for proxy in proxyList:
    #             yield proxy

#执行爬取并保存类
POOL_UPPER_THRESHOLD = 10000
class Getter():
    def __init__(self):
        self.redis = RedisClient()
        self.crawler = Crawler()

    def is_over_threshold(self):
        if self.redis.count() >= POOL_UPPER_THRESHOLD:
            return True
        else:
            return False

    def run(self):
        if not self.is_over_threshold():
            for index in range(self.crawler.__CrawlFuncCount__):    #self.crawler.__CrawlFuncCount__:开启了的爬取代理网站函数个数
                crawlFuncName = self.crawler.__CrawlFunc__[index]    #self.crawler.__CrawlFunc__[callback_label:开启了的爬取代理网站函数的列表，这里在遍历索引取值
                proxiesList = self.crawler.get_proxies(crawlFuncName)    #将爬取代理网站函数名传回去，并调用这个爬取函数，对目标代理网站爬取ip
                for proxy in proxiesList:
                    self.redis.add(proxy)

if __name__ == '__main__':
    getter = Getter()
    getter.run()