'''
自己的第一个类，用于发送短信
'''
from myClass.runNum import RunNum
class MobilePhone(object):
    runNum = RunNum()
    runNumber = runNum.verificationCode1(6)
    def __init__(self, number, text='您的验证码是：%s。请不要把验证码泄露给其他人。' % runNumber):
        self.number = number
        self.text = text

    def sendMassage(self):
        import http.client
        import urllib
        host = "106.ihuyi.com"
        sms_send_uri = "/webservice/sms.php?method=Submit"
        account = "C10780844"
        password = "d5cb4462b9db850e1e3dc0427f2dc838"
        params = urllib.parse.urlencode({'account': account, 'password': password, 'content': self.text, 'mobile': self.number, 'format': 'json'})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        conn = http.client.HTTPConnection(host, port=80, timeout=30)
        conn.request("POST", sms_send_uri, params, headers)
        response = conn.getresponse()
        response_str = response.read()
        conn.close()
        #print(response_str)
        print('验证码已发送')

if __name__ == '__main__':
    mobilePhon = MobilePhone('17311328850')
    mobilePhon.sendMassage()