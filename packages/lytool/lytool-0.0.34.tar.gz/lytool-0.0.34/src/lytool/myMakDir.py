import os
def myMkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == '__main__':
    path = './父级/子级'
    myMkdirs(path)  # 创建子级文件夹，如果父级不存在，会自动创建