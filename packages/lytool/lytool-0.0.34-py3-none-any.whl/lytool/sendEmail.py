class sendEmail(object):
    def __init__(self, sender, password, text, title, *addresseeList):
        self.sender = sender #chenyilong112233@163.com
        self.password = password #135cylpsx
        self.text = text #邮件内容
        self.title = title #邮箱标题
        self.addresseeList = list(addresseeList) #收件人

    def sendemail(self):
        import smtplib #发邮件的库
        from email.mime.text import MIMEText #邮件文本
        #SMTP服务器
        SMTPServer = 'smtp.163.com'
        #发件者的地址
        sender = self.sender
        #发送者邮箱的密码(授权码)
        passwd = self.password
        #设置发送的内容
        message = self.text
        #字符串转邮件文本
        msg = MIMEText(message)
        #标题
        msg['Subject'] = self.title
        #发送者
        msg['From'] = self.sender
        #创建SMTP服务器，即链接服务器,相当于打开163的登陆界面
        mailServer = smtplib.SMTP(SMTPServer, 25) #邮件的端口号都是25，以后设置自己的端口号要超过1024，因为0-1024都是被系统占用的
        #登陆邮箱
        mailServer.login(sender, passwd)
        #发送邮件
        mailServer.sendmail(self.sender, self.addresseeList, msg.as_string()) #参数1：发送者;参数2：收件者列表;参数3：一个函数，将列表中的字符串转换成邮件形式的字符串
        #退出邮箱
        mailServer.quit()

if __name__ == '__main__':
    send_mail = sendEmail('chenyilong112233@163.com', '135cylpsx', '老婆记得吃饭哦', '老公的祝福', '396216857@qq.com', '417217170@qq.com')
    send_mail.sendemail()