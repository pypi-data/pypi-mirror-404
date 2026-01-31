import re
class RegularExpression(object):
    def checkMobile(self, str):
        regular = re.compile(r'^1(([3578]\d)|(47))\d{8}$')
        re_Mobile = regular.match(str)
        if re_Mobile == None:
            return False
        return True

    def getMobile(self, str):
        regular = re.compile(r'1(([3578]\d)|(47))\d{8}')
        re_Mobile = regular.finditer(str)
        return re_Mobile

    def checkQQ(self, str): #6位到10位的数字
        regular = re.compile(r'^[1-9]\d{5,9}$')
        re_qq = regular.match(str)
        if re_qq == None:
            return False
        return True

    def getQQ(self, str): #6位到10位的数字
        regular = re.compile(r'[1-9]\d{5,9}')
        re_QQ = regular.findall(str)
        return re_QQ

    def checkMail(self, str): #417217170@qq.com
        regular = re.compile(r'^(\w{1,})?@(\w{2,3})\.([a-z]{2,})$')
        re_Mail = regular.match(str)
        if re_Mail == None:
            return False
        return True

    def getMail(self, str): #417217170@qq.com
        regular = re.compile(r'(\w{1,})?@(\w{2,3})\.([a-z]{2,})')
        re_Mail = regular.finditer(str)
        return re_Mail

    def checkPhone(self, str): #028-85652706
        regular = re.compile(r'^(\d{3})-(\d{8})$')
        re_Phon = regular.match(str)
        if re_Phon == None:
            return False
        return True

    def getPhone(self, str):
        regular = re.compile(r'(\d{3})-(\d{8})')
        re_Phon = regular.finditer(str)
        return re_Phon

    def checkUser(self, str): #6-12位的数字、字母、下划线
        regular = re.compile(r'^(\w{6,12})$')
        re_Url = regular.match(str)
        if re_Url == None:
            return False
        return True

    def getUser(self, str): #6-12位的数字、字母、下划线
        regular = re.compile(r'(\w{6,12})')
        re_Url = regular.finditer(str)
        return re_Url

    def checkPassWord(self, str): #6-12位的数字、字母、下划线
        regular = re.compile(r'^(\w{6,12})$')
        re_PassWord = regular.match(str)
        if re_PassWord == None:
            return False
        return True

    def getPassWord(self, str):
        regular = re.compile(r'(\w{6,12})')
        re_PassWord = regular.finditer(str)
        return re_PassWord

    def checkIp(self, str): #171.221.146.39
        regular = re.compile(r'^((25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))\.){3}(25[0-5]|2[0-4]\d|((1\d{2})|([1-9]?\d)))$')
        re_Ip = regular.match(str)
        if re_Ip == None:
            return False
        return True

    def getIp(self, str):
        regular = re.compile(r'(((http|https|ftp)://)(([a-zA-Z0-9\._-]+\.[a-zA-Z]{2,6})|([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}))(:[0-9]{1,4})*(/[a-zA-Z0-9\&%_\./-~-]*)?)')
        re_Ip = regular.finditer(str)
        return re_Ip

    def checkUrl(self, str):#https://www.pclady.com.cn/tlist/88810.html
        regular = re.compile(r'^(((http|https|ftp)://)(([a-zA-Z0-9\._-]+\.[a-zA-Z]{2,6})|([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}))(:[0-9]{1,4})*(/[a-zA-Z0-9\&%_\./-~-]*)?)$')
        re_Url = regular.match(str)
        if re_Url == None:
            return False
        return True

    def getUrl(self, str):#https://www.pclady.com.cn/tlist/88810.html
        regular = re.compile(r'(((http|https|ftp)://)(([a-zA-Z0-9\._-]+\.[a-zA-Z]{2,6})|([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}))(:[0-9]{1,4})*(/[a-zA-Z0-9\&%_\./-~-]*)?)')
        re_Url = regular.findall(str)#是用这个正则表达式，会将url拆分成片段，想要获得完整url，只需要在最外层打上小空号即可
        return re_Url #返回的是列表元组，url在 [i[0] for i in re_Url[0]]

if __name__ == '__main__':
    myre = RegularExpression()
    print(myre.checkQQ('417710132412341234'))
