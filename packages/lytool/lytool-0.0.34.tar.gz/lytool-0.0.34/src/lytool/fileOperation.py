#文件复制
import os
class FileOperation(object):
    def fileCopyFor(self, path, toPath):
        fileList = os.listdir(path)
        for fileName in fileList:
            absFilePath = os.path.join(path, fileName)
            absToFilePath = os.path.join(toPath, fileName)
            with open(absFilePath, 'r') as f:
                context = f.read()
            with open(absToFilePath, 'w') as f:
                f.write(context)

#文件移动
import time, os
from multiprocessing import Pool

def MoveFile(absPath, absToPath):
    with open(absPath, 'rb') as f:
        context = f.read()
    with open(absToPath, 'wb') as f:
        f.write(context)
    os.remove(absPath)

if __name__ == '__main__':
    path = r'C:\Users\surface\Videos\爬虫完整教学\31369828_{}_0.flv'
    toPath = r'C:\Users\surface\Videos\爬虫教学-清华牛人\{}.flv'
    pp = Pool()
    startTime = time.time()
    for i in range(1, 595): #595
        absPath = path.format(i)
        absToPath = toPath.format(i)
        print(absPath)
        print(absToPath)
        pp.apply_async(MoveFile, args=(absPath, absToPath))
    pp.close()
    pp.join()
    endTime = time.time()
    print(endTime - startTime)