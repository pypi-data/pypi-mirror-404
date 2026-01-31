import time
from datetime import datetime
from dateutil import parser


class MyTime():
    def __init__(self):
        self.currentTime()

    def currentTime(self):
        '''获取当前时间'''
        self.current_time = parser.parse(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        return self.current_time

    def currentSubTimeForDay(self, time):
        '''计算今日-时间的天数'''
        diffTime = self.current_time - time
        return diffTime.days

    def timeSubCurrentForDay(self, time):
        '''计算今日-时间的天数'''
        diffTime = time - self.current_time
        return diffTime.days

    def beforeAfterTime(self, before_time, after_time):
        '''计算自定义两个的时间差'''
        diffTime = after_time - before_time
        return diffTime.days

    def howOld(self, birthYear):
        '''计算你多大了'''
        currentYear = self.currentTime().year
        old = int(currentYear) - int(birthYear)
        return old

    def stampToDateTime(self, datesteam):
        '''时间戳转年月日时分秒'''
        return datetime.utcfromtimestamp(datesteam / 1000)

    def stampToDate(self, timestamp):
        '''时间戳转年月日'''
        dt_object = datetime.fromtimestamp(timestamp/ 1000)
        formatted_date = dt_object.strftime('%Y-%m-%d')
        return formatted_date

if __name__ == '__main__':
    myTime = MyTime()

    # print(myTime.currentTime())

    # before_time = parser.parse('2021/08/31 08:53:01')
    # diffDays = myTime.current_diffTime(before_time)
    # print(diffDays)

    # after_time = parser.parse('2021/09/30')  # 之后时间
    # diffDays = myTime.before_after_time(before_time, after_time)
    # print(diffDays)
    #
    # print(myTime.currentTime())
    #
    # old = myTime.howOld('1988')
    # print(old)

    timestamp = 1700291277000  # 毫秒为单位的时间戳
    print(myTime.stampToDate(timestamp))  # 得到datetime.datetime的年月日时分秒


