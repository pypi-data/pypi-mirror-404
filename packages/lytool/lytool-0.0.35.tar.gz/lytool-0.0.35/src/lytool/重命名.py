import os
import shutil

#将指定文件夹中的所有文件，剪切到另一指定文件夹中并且重命名（从零开始）

path1 = r'.\1' #源文件所在文件夹路径
path2 = r'.\2' #重命名后文件的存放路径

n = 0
for fileName in os.listdir(path1):
    absFilePath = os.path.join(path1, fileName)
    shutil.copyfile(absFilePath, os.path.join(path2, '{}.html'.format(str(n))))
    n += 1

shutil.rmtree(path1)