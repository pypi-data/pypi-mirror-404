import base64
from hashlib import md5
from PIL import Image

class ImageTool:
    def toB64(self, imagePath):
        '''
        功能：图片转base64
        imagePath: 图片地址
        return: base64编码
        '''
        with open(imagePath, "rb") as f:
            b64Str = bytes.decode(base64.b64encode(f.read()))
        return b64Str


    def toImage(self, base64str, absFilePath):
        '''
        功能：base64转图片
        base64str: string '/sdfasdf/asdfasf=='
        absFilePath: string '/var/www/html/images/imageName.png'
        '''
        b64 = base64.b64decode(base64str)
        with open(absFilePath, 'wb') as f:
            f.write(b64)

    def toMd5(self, data):
        '''
        功能: b64转md5
        '''
        return md5(data.encode('utf8')).hexdigest()

    def losslessCompression(self, input_file, output_file):
        '''
        无损压缩
        :param input_file: str 文件路径
        :param output_file: str  文件路径
        :return:
        '''
        optipng_path = r'D:\optipng-0.7.8-win64\optipng.exe'  # 确保路径正确
        input_file = os.path.abspath(input_file)
        output_file = os.path.abspath(output_file)
        cmd = f'"{optipng_path}" -o7 -out "{output_file}" "{input_file}"'
        subprocess.run(cmd, shell=True)

    def to_webp(self, input_path, output_path, quality=80):
        img = Image.open(input_path)
        img.save(output_path, 'WEBP', quality=quality, method=6)

if __name__ == '__main__':
    itl = ImageTool()

    fileName = "添加好友.png"
    suffix = fileName.split('.')[-1]
    b64Str = itl.toB64(f"./{fileName}")
    NewFilename = itl.toMd5(b64Str) + f'.png'
    itl.toImage(b64Str, NewFilename)


    # 无损压缩
    output_file = r'./2.png'
    input_file = r'./1.png'
    itl.losslessCompression(input_file, output_file,)
