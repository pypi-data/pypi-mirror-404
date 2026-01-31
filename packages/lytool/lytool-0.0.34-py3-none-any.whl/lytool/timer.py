import time
import random
randomtime = random.randint(1, 59)
if time.strftime('%H:%M:%S', time.localtime()) == '9:{}:{}'.format(randomtime, randomtime):
    time.sleep(39600)