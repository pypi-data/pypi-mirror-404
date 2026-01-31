from hashlib import md5
def myMd5(data):
    return md5(data.encode('utf8')).hexdigest()

if __name__ == '__main__':
    print(myMd5('123'))