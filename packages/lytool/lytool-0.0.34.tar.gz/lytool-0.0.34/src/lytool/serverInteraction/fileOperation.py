import paramiko
import os

class FileOperation:
    def __init__(self, host, port, userName, password):
        # 创建 SSH 客户端
        self.client = paramiko.SSHClient()
        # 自动添加主机密钥
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接到服务器
        self.host = host
        self.client.connect(self.host, port, userName, password, timeout=60)
        # 使用 SFTP 进行文件上传
        self.sftp = self.client.open_sftp()
        # 远端地址
        # self.remotePath = remotePath

    def upLoadFile(self, fileLocalPath, remotePath):
        '''本地文件上传到服务器'''
        if not os.path.exists(fileLocalPath):
            print(f"本地文件不存在")
            return
        # self.sftp.put(fileLocalPath, os.path.join(self.remotePath, fileLocalPath.split('\\')[-1]))
        fileName = fileLocalPath.split('\\')[-1]
        serverPath = remotePath + '/' + fileName
        print(f'【正在上传】{fileLocalPath}')
        self.sftp.put(fileLocalPath, serverPath)
        print(f'【服务器文件路径】{serverPath}')
        serverAddress = f'https://www.liangyu.online/static/{remotePath.split("static/")[-1]}/{fileName}'
        print(f'【服务器地址】{serverAddress}')
        return serverAddress

    def disconnect(self):
        # 关闭 SFTP 和 SSH 连接
        self.sftp.close()
        self.client.close()
        

if __name__ == '__main__':
    fileOperation = FileOperation('150.158.25.233', 22, 'ubuntu', '135cylpsx4848@')
    imageServerAddress = fileOperation.upLoadFile('.\\detail_755014be9fac937d7b3ab1f860fb619d_0.png', '/usr/share/nginx/html/static/images/ly/product')