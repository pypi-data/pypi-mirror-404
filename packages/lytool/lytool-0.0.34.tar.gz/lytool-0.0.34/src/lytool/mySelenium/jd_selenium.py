from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from lxml import etree
import time
import random
from myClass.get_selenium_cookies_dict import get_my_cookie_list
from myClass.myPickle import *

class MySelenium():
    def __init__(self, isHeadless='No'):
        options = Options()
        if isHeadless == 'Yes':
            # 添加属性无头
            options.add_argument('--headless')

        # 添加本地代理
        # options.add_argument('--proxy--server=127.0.0.1:8080')

        # 设置请求头
        ua = 'Mozilla/5.0 (X11; OpenBSD i386) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'
        options.add_argument('user-agent='+ua)

        # 屏蔽'CHROME正受到组件控制'的提示
        options.add_experimental_option('excludeSwitches', ['enable-automation'])

        # 屏蔽密码保护
        prefs = {}
        prefs["credentials_enable_service"] = False
        prefs["profile.password_manager_enabled"] = False
        options.add_experimental_option("prefs", prefs)

        self.browser = webdriver.Chrome(options=options)

        self.browser.set_page_load_timeout(10)
        with open(r'C:\Users\justin\Desktop\yilong\myClass\mySelenium\stealth.min.js') as f:
            js = f.read()
        print(type(js))
        self.browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": js
        })
        '''
        window.navigator.webdriver
        '''
        self.browser.implicitly_wait(10)  # 开启隐式等待，对全局开启等待，每操作一次，系统会等待元素加载，直到元素加载完毕，如果等待10秒后元素还未出现，则抛出异常
        self.browser.maximize_window()  # 最大化浏览器

    def myTree(self, path='./1.html'):
        page_source = self.browser.page_source  # 获取页面源码
        with open(path, 'w', encoding='utf8') as f:
            f.write(page_source)
        tree = etree.HTML(page_source, etree.HTMLParser())  # 创建xpath操作树
        time.sleep(random.random() * 10)
        return tree

    def myClose(self):
        self.browser.close()
        self.browser.quit()

    def myJs(self, command):
        if command == '滑动到底部':
            self.browser.execute_script('window.scrollTO(0, document.body.scrollHeight)')
        elif command == '滑动到顶部':
            self.browser.execute_script('window.scrollTO(0, document.body.scrollHeight)')

    def myWait(self, xpath):
        '''
        一直等待指定元素，每过0.5秒查看一次，该元素是否加载完毕，如果超过最长时间50s，则抛出异常
        '''
        condition = EC.visibility_of_element_located((By.XPATH, xpath))
        WebDriverWait(driver=self.browser, timeout=20, poll_frequency=0.5).until(condition)

    def switch_handle(self):
        # 切换选项卡
        first_win = self.browser.current_window_handle
        all_windows = self.browser.window_handles
        for win in all_windows:
            if win != first_win:
                self.browser.switch_to.window(win)
                print('切换成功')

    def scrollIntoView(self, xpath):
        '''
        向下滚动到某个对象课件
        '''
        obj = self.browser.find_elements_by_css_selector(xpath)
        self.browser.execute_script("arguments[0].scrollIntoView();", obj)

    def iframe(self, iframeXpath):
        '''
        iframe是前端的嵌套标签，可以将一个完整的html代码嵌套到另一个html中
        当遇到iframe标签时，需要进入iframe标签，再用xpath获取内层html中的元素
        在浏览器中使用xpath工具，是无法正常显示对应元素的，但确实能够被获取
        iframe标签的id极有可能使用动态id，刷新一次<iframe id='随机'>,id就会变化，需要用其他属性来获取iframe标签
        '''
        iframe = self.browser.find_element(by=By.XPATH, value=iframeXpath)
        self.browser.switch_to.frame(iframe)

    def set_cookies(self, domain, cookies, url):
        self.browser.get(url)
        self.browser.delete_all_cookies()

        # cookies_list = get_my_cookie_list(domain, cookies)
        '''
        手动添加cookies到下面列表中
        '''
        cookies_list = []
        for cookie in cookies_list:
            if 'expiry' in cookie:
                # dict支持pop的删除函数
                del cookie['expiry']
            self.browser.add_cookie(cookie)
        self.browser.refresh()  # 刷新浏览器

    def get_cookies(self, url):
        # 获取cookies
        self.browser.get(url)
        '''
        手机扫码登录
        '''
        time.sleep(10)
        cookies = self.browser.get_cookies()
        print(cookies)
        time.sleep(5)
        self.myClose()
        return cookies

    # 电子发票换开
    def electronic_invoice_reissue(self):
        url = 'http://jzsc.mohurd.gov.cn/data/company'
        self.browser.get(url)
        time.sleep(100)

if __name__ == '__main__':
    mySelenium = MySelenium('No')
    mySelenium.sikuyi()


