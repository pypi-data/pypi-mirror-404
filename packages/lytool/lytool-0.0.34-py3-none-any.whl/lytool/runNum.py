import random
import itertools
from functools import reduce

class RunNum(object):
    def verificationCode1(self, digit):
        str_ = ''
        runNumber = random.randrange(3)
        for i in range(digit):
            if runNumber == 0:#小写
                ch = chr(random.randrange(ord('a'), ord('z') + 1))
                str_ += ch
            elif runNumber == 1:#大写
                ch = chr(random.randrange(ord('A'), ord('Z') + 1))
                str_ += ch
            elif runNumber == 2:#数字
                ch = chr(random.randrange(ord('0'), ord('9') + 1))
                str_ += ch
        return str_

    def verificationCode2(self, digit):
        str_ = (''.join(x) for x in itertools.product('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', repeat=digit))
        return str_[0]