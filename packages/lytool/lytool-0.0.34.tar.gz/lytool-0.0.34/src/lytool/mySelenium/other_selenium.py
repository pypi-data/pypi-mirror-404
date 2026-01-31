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
        # print(type(js))
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

    # 设置cookies并登录
    def set_cookies(self, url, cookies):
        self.browser.get(url)
        self.browser.implicitly_wait(10)
        self.browser.delete_all_cookies()
        cookies_list = cookies
        for cookie in cookies_list:
            if 'sameSite' in cookie:
                if cookie['sameSite'] == 'None':
                    cookie['sameSite'] = 'Strict'
            if 'expiry' in cookie:
                # dict支持pop的删除函数
                del cookie['expiry']
            self.browser.add_cookie(cookie)
        self.browser.refresh()  # 刷新浏览器
        self.browser.get(url)

    # 获取cookies
    def get_cookies(self):
        '''
        扫码登录
        '''
        time.sleep(10)
        cookies = self.browser.get_cookies()
        time.sleep(5)
        self.browser.close()
        # self.myClose()
        return cookies

    # 妙手
    def miaoshou(self):
        url = 'http://www.91miaoshou.com/'
        self.browser.get(url)
        self.myWait('/html/body/div[4]/div[2]/ul[2]/li[1]/a')
        self.browser.find_element(by=By.XPATH, value='/html/body/div[4]/div[2]/ul[2]/li[1]/a').click()
        self.switch_handle()
        self.myWait('//*[@id="J_login"]/div[1]/input')
        self.browser.find_element(by=By.XPATH, value='//*[@id="J_login"]/div[1]/input').send_keys('18086829907')
        self.myWait('//*[@id="J_login"]/div[2]/input')
        self.browser.find_element(by=By.XPATH, value='//*[@id="J_login"]/div[2]/input').send_keys('135cylpsx')
        self.myWait('//*[@id="J_login"]/div[3]/span')
        self.browser.find_element(by=By.XPATH, value='//*[@id="J_login"]/div[3]/span').click()
        self.myWait('//*[@id="app"]/section/section/main/div[1]/div[4]/div/div/div[1]/button/i')
        self.browser.find_element(by=By.XPATH, value='//*[@id="app"]/section/section/main/div[1]/div[4]/div/div/div[1]/button/i').click()
        self.myWait('//*[@id="app"]/section/section/main/div[1]/div[4]/div/div/div[1]/button/i')
        self.browser.find_element(by=By.XPATH, value='//*[@id="app"]/section/section/main/div[1]/div[4]/div/div/div[1]/button/i').click()
        self.myWait('//*[@id="app"]/section/section/main/div[1]/div[4]/div/div/div[1]/button/i')
        self.browser.find_element(by=By.XPATH, value='//*[@id="app"]/section/section/main/div[1]/div[4]/div/div/div[1]/button/i').click()
        self.myWait('//*[@id="app"]/section/section/main/div[1]/div[4]/div/div/div[1]/button/i')
        self.browser.find_element(by=By.XPATH, value='//*[@id="app"]/section/section/main/div[1]/div[4]/div/div/div[1]/button/i').click()
        self.myWait('//*[@id="pane-shopee"]/div/div/div[1]/div/div/div[1]/div')
        self.browser.find_element(by=By.XPATH, value='//*[@id="pane-shopee"]/div/div/div[1]/div/div/div[1]/div').click()
        url_commodity = input('请输入url：')
        self.myWait('//*[@id="guide-step-menu-collect-input"]/div/div[1]/div/textarea')
        self.browser.find_element(by=By.XPATH, value='//*[@id="guide-step-menu-collect-input"]/div/div[1]/div/textarea').send_keys(url_commodity)
        # self.myWait('//*[@id="pane-linksCopy"]/div/div[4]/div/div[3]/div/button[2]/span')
        # self.browser.find_element(by=By.XPATH, value='//*[@id="pane-linksCopy"]/div/div[4]/div/div[3]/div/button[2]/span').click()
        self.myWait('//*[@id="pane-linksCopy"]/div/div[2]/div/button')
        self.browser.find_element(by=By.XPATH, value='//*[@id="pane-linksCopy"]/div/div[2]/div/button').click()
        self.myWait('//*[@id="pane-linksCopy"]/div/div[4]/div/div[3]/div/button[2]')
        self.browser.find_element(by=By.XPATH, value='//*[@id="pane-linksCopy"]/div/div[4]/div/div[3]/div/button[2]').click()
        self.myWait('//*[@id="app"]/section/section/main/div[1]/div[2]/div[3]/div[2]/div[3]/table/tbody/tr[1]/td[7]/div/div[1]/button[1]')
        self.browser.find_element(by=By.XPATH, value='//*[@id="app"]/section/section/main/div[1]/div[2]/div[3]/div[2]/div[3]/table/tbody/tr[1]/td[7]/div/div[1]/button[1]').click()

        tree = self.myTree()

        # self.myWait('//*[@id="app"]/section/section/main/div[1]/div[2]/div[3]/div[2]/div[3]/table/tbody/tr[1]/td[2]/div/div/div[2]/a')
        # title = tree.xpath('//*[@id="app"]/section/section/main/div[1]/div[2]/div[3]/div[2]/div[3]/table/tbody/tr[1]/td[2]/div/div/div[2]/a/text()')
        # print(title)

    # 1688登录
    def a1688_save_cookie(self):
        # 访问首页
        self.browser.get('https://www.1688.com')

        # 跳转登录页面
        time.sleep(random.random()*10)
        self.browser.find_element(by=By.XPATH, value='//*[@id="alibar"]/div[1]/div[2]/ul/li[3]/a').click()

        # 进入iframe内部
        self.iframe('//*[@id="loginchina"]/iframe')
        time.sleep(random.random()*10)
        '''
        c18086829907@163.com 135cylpsx4848@
        1688批量爬取商品url
        '''
        self.browser.find_element(by=By.XPATH, value='//*[@id="fm-login-id"]').send_keys('c18086829907@163.com')  # 输入账号
        time.sleep(random.random()*10)
        self.browser.find_element(by=By.XPATH, value='//*[@id="fm-login-password"]').send_keys('135cylpsx4848@')  # 输入密码
        time.sleep(random.random()*10)

        # 解决滑块
        slide_block = self.browser.find_element(by=By.XPATH, value='//*[@id="nc_1_n1z"]')
        if (slide_block.is_displayed()):
            # 点击移动滑块
            action = ActionChains(self.browser)
            action.click_and_hold(on_element=slide_block)
            action.move_by_offset(xoffset=258, yoffset=0)
            action.pause(0.5).release().perform()  # perform指定动作链
        self.browser.find_element(by=By.XPATH, value='//*[@id="login-form"]/div[4]/button').click()
        time.sleep(5)
        if "login_unusual" in self.browser.current_url:
            print("gg了，要手机验证码了，救命啊啊啊啊啊")
            input("输入手机验证码啦：")

        # 保存cookie
        print(self.browser.get_cookies())
        cookies = '; '.join(item for item in [item["name"] + "=" + item["value"] for item in self.browser.get_cookies()])
        with open('./cookies.txt', 'w', encoding='utf-8') as file:
            file.write(cookies)
            print("cookie写入成功：", cookies)
        self.myClose()

    # 1688下载
    def a1688(self):
        # with open('./cookies.txt', 'r', encoding='utf-8') as f:
        #     cookies = f.read()
        # self.browser.add_cookie(cookies[0])  # 添加cookies
        # time.sleep(random.random()*10)
        self.browser.get('https://detail.1688.com/offer/598717932683.html?spm=a260k.dacugeneral.home2019rec.1.6633436cLLlujv&tracelog=p4p&clickid=d5c389039b26436588db3eb50d5a9622&sessionid=44a95e47ae845d7e3c9e93abe1bbb0c9')  # 访问产品
        self.browser.find_element(by=By.XPATH, value='//*[@id="fm-login-id"]').send_keys('c18086829907@163.com')  # 输入账号
        self.myWait('//*[@id="fm-login-password"]')
        self.browser.find_element(by=By.XPATH, value='//*[@id="fm-login-password"]').send_keys('135cylpsx4848@')  # 输入密码
        self.browser.find_element(by=By.XPATH, value='//*[@id="login-form"]/div[4]/button').click()  # 点击登录
        self.browser.save_screenshot('./1688_image.png')  # 截图
        # time.sleep(random.random()*10)
        # self.scrollIntoView('//*[@id="site_footer"]/div/div[2]/div/div[2]/div/p[3]/a[1]')  # 向下滚动值到某物出现

    # 百度测试
    def baidu1(self):
        # 有头浏览器-百度
        self.browser.get('https://www.baidu.com')
        self.browser.find_element(by=By.XPATH, value='//input[@id="kw"]').send_keys('美女')  # 输入
        self.myWait('//input[@id="su"]')  # 显示等待指定元素的出现
        self.browser.find_element(by=By.XPATH, value='//input[@id="su"]').click()  # 点击
        next_btn = self.browser.find_element(by=By.XPATH, value='//*[@id="page"]/div/a[10]')
        ActionChains(self.browser).move_to_element(next_btn).click().perform()  # 滚动到下一页位置并点击
        tree = self.myTree()  # 获取网页源码
        print(tree.xpath('//*[@id="11"]/h3/a/@href'))
        self.browser.save_screenshot('./baidu_image.png')
        print(self.browser.get_cookies())
        self.myClose()  # 关闭浏览器

    # 百度测试
    def baidu2(self):
        cookies_baidu = 'BIDUPSID=F9789D624DAA5852480C89941BA645E0; PSTM=1616248343; BAIDUID=F9789D624DAA5852CE7FC82030239C37:FG=1; BD_UPN=12314753; __yjs_duid=1_2df4bc05440f0e15a21a96f9ffa7baec1619514497839; ispeed_lsm=2; MCITY=-%3A; BAIDUID_BFESS=F9789D624DAA5852CE7FC82030239C37:FG=1; __yjs_st=2_N2ViNDFiMmRiNjkwZmM3ODc4MzViNTYyMTZjZTBkOTdhZTJkOTA0NjY4YmY0YWM1NzY4ZmU5MWViZGQ0NjdkODU0Yzg4MzhmNTA3ZTBhNmU4OGMzNzE0NTk3YTkxNDQwNTdlYTUwZWUzMGJjNDQ2YmYzNzBhODM0NmIxYjlmODRkMjFmODNmMDIxOTI1ZDY3MWYyZGUyMzZiOTE0NjcwOTM4NmQwMmQ2NzNhNmFhN2U1OWYzZDNjNGUxNDA1NmNhYmIzY2U2ZTIyNzhlNDNmZjg5OWEzY2YxNTJiZDE3M2MzMTgwMDJjOTBlOTA5MDMyY2M0NGYxMGMwZmUzOGU4N2NjNzJkZWQ2Zjk3ZGQ2NzQxNGJkNjkzZDFhYzc0YTU5XzdfNDU1N2NkZjM=; Hm_lvt_aec699bb6442ba076c8981c6dc490771=1629704730; sug=3; sugstore=1; ORIGIN=0; bdime=0; BDUSS=WNLZkF1T2l4aHFwUGpKcVBNSy14Vm83VEtEN0dNTHRuWTdIVHY1OXRJaEI1VXBoRVFBQUFBJCQAAAAAAAAAAAEAAACiOdSjwfrBvNPqtcTL2LLEv-IAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEFYI2FBWCNha; BDUSS_BFESS=WNLZkF1T2l4aHFwUGpKcVBNSy14Vm83VEtEN0dNTHRuWTdIVHY1OXRJaEI1VXBoRVFBQUFBJCQAAAAAAAAAAAEAAACiOdSjwfrBvNPqtcTL2LLEv-IAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEFYI2FBWCNha; BDORZ=FFFB88E999055A3F8A630C64834BD6D0; COOKIE_SESSION=4197_0_5_5_10_35_1_2_5_5_2_0_4147_0_25_0_1629712451_0_1629712426%7C5%230_0_1629712426%7C1; BDRCVFR[sik10YimRpn]=EBD6F1bEM2tXZKdrHn8mvqV; BD_HOME=1; H_PS_PSSID=31254_26350; delPer=0; BD_CK_SAM=1; PSINO=7; H_PS_645EC=2ef0vAxShrV7IW5KKVGbeKuamZVPDe07VU9yL%2FV7A8gheJuU6gOAKkjGPy4rAffDQ5KdeKz7paYh; BA_HECTOR=85a5ah0g0la12k2he01gi72qt0r; BDSVRTM=0'
        self.set_cookies('.baidu.com', cookies_baidu)

        self.browser.get('https://www.baidu.com')
        # print(self.browser.get_cookies())
        time.sleep(1000)
        self.myClose()  # 关闭浏览器

    # 360邮箱模拟登录
    def email_360(self):
        '''
        360模拟登录
        '''
        self.browser.get('https://mail.163.com/')
        time.sleep(random.random()*10)
        self.iframe('//iframe[@scrolling="no"]')  # 进入iframe
        self.browser.find_element(by=By.XPATH, value='//input[@name="email"]').send_keys('c18086829907')
        time.sleep(random.random() * 10)
        self.browser.find_element(by=By.XPATH, value='//input[@name="password"]').send_keys('135cylpsx4848@')
        time.sleep(random.random() * 10)
        self.browser.find_element(by=By.XPATH, value='//a[@id="dologin"]').click()
        time.sleep(random.random()*10)
        self.browser.close()
        self.browser.quit()

    # 豆瓣电影
    def douban_movie(self):
        domain = '.douban.com'
        cookies_douban = 'll="118318"; bid=ICuIvj3BSYg; _vwo_uuid_v2=D9A5BD54775C0A8ADA196ED7DD237E303|8357de64c78dca92d17b68504bf9f1c1; ct=y; gr_user_id=1d391c67-6d39-4aef-a805-385b39eb430d; _ga=GA1.1.1852380685.1624613315; _ga_RXNMP372GL=GS1.1.1628168451.1.1.1628168489.0; __yadk_uid=Xm3InJI7rtOYaiiJQ2J2Lj4HCKR2jaxO; viewed="4913064_35438602"; __utma=30149280.1852380685.1624613315.1628930406.1629721717.7; __utmz=30149280.1629721717.7.6.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; __utmc=30149280; __utmt=1; dbcl2="172123593:j5u/XDBOMV8"; ck=nAmJ; ap_v=0,6.0; push_noty_num=0; push_doumail_num=0; __utmv=30149280.17212; __gads=ID=90244c96a19371be-220a66801acb0008:T=1625047326:RT=1629721870:S=ALNI_MZwGuXTny2lc6fsMvQ2DEKbGR-xqw; __utmb=30149280.17.10.1629721717; __utma=223695111.1154555244.1625047327.1628930406.1629721879.6; __utmb=223695111.0.10.1629721879; __utmc=223695111; __utmz=223695111.1629721879.6.5.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/gallery/; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1629721880%2C%22https%3A%2F%2Fwww.douban.com%2Fgallery%2F%22%5D; _pk_id.100001.4cf6=3f95e8a8b90a65eb.1625047326.6.1629721880.1628930649.; _pk_ses.100001.4cf6=*'
        self.set_cookies(domain, cookies_douban)
        self.browser.get('https://movie.douban.com/')
        self.browser.save_screenshot('./douban.png')  # 截图

    # 58登录
    def tc58_login(self):
        self.browser.get('https://sz.58.com/searchjob/?pts=1629884554040')
        self.myWait('//*[@id="mask_body"]/div[1]')
        print('等待登录')
        time.sleep(100)
        print('登录成功')
        self.myTree()

    # 全国建筑市场监管公共服务平台
    def sikuyi(self):
        url = 'http://jzsc.mohurd.gov.cn/data/company'
        self.browser.get(url)
        time.sleep(100)

    # 起点获取cookies
    def qd_get_cookies(self, url):
        self.browser.get(url)
        self.browser.implicitly_wait(10)
        time.sleep(1)
        self.browser.find_element_by_xpath('//*[@id="login-btn"]').click()
        self.iframe('//*[@id="loginIfr"]')
        time.sleep(1)
        self.browser.find_element_by_xpath('//*[@id="j_loginTab"]/ul/li[3]').click()
        time.sleep(10)
        cookies = self.get_cookies()
        print(cookies)
        return cookies

    # 起点模拟登录
    def qd_login(self):
        url = 'https://www.qidian.com/'
        # 获取cookies
        # cookies = self.qd_get_cookies(url)
        cookies = [{'domain': '.qidian.com', 'expiry': 1636341818, 'httpOnly': False, 'name': 'e1', 'path': '/', 'secure': False, 'value': '%7B%22pid%22%3A%22qd_p_qidian%22%2C%22eid%22%3A%22qd_A06%22%2C%22l1%22%3A1%7D'}, {'domain': '.qidian.com', 'expiry': 1636341818, 'httpOnly': False, 'name': 'e2', 'path': '/', 'secure': False, 'value': ''}, {'domain': '.qidian.com', 'expiry': 1633749877, 'httpOnly': False, 'name': '_gat_gtag_UA_199934072_2', 'path': '/', 'secure': False, 'value': '1'}, {'domain': 'www.qidian.com', 'httpOnly': False, 'name': '_yep_uuid', 'path': '/', 'secure': False, 'value': '6b2ef6ba-baa7-fbf0-1c59-aa15df5e272a'}, {'domain': '.qidian.com', 'expiry': 1696821817, 'httpOnly': False, 'name': '_ga', 'path': '/', 'secure': False, 'value': 'GA1.2.477961808.1633749817'}, {'domain': '.qidian.com', 'expiry': 1665285817, 'httpOnly': False, 'name': '_csrfToken', 'path': '/', 'secure': False, 'value': 'iqXiUnqXENDSS8JEHAGxjv1KLaQUvAkYqdlnXYCh'}, {'domain': '.qidian.com', 'expiry': 1696850617, 'httpOnly': False, 'name': 'newstatisticUUID', 'path': '/', 'sameSite': 'None', 'secure': True, 'value': '1633749815_1209936850'}, {'domain': '.qidian.com', 'expiry': 1633836217, 'httpOnly': False, 'name': '_gid', 'path': '/', 'secure': False, 'value': 'GA1.2.496967009.1633749818'}, {'domain': '.qidian.com', 'expiry': 1696821817, 'httpOnly': False, 'name': '_ga_PFYW0QLV3P', 'path': '/', 'secure': False, 'value': 'GS1.1.1633749816.1.0.1633749816.0'}, {'domain': '.qidian.com', 'expiry': 1696821817, 'httpOnly': False, 'name': '_ga_FZMMH98S83', 'path': '/', 'secure': False, 'value': 'GS1.1.1633749816.1.0.1633749816.0'}]
        self.set_cookies(url, cookies)

if __name__ == '__main__':
    mySelenium = MySelenium()
    mySelenium.qd_login()


