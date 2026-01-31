import qrcode
import os
from pyzbar.pyzbar import decode
from PIL import Image

class MyQRcode():
    def __init__(self, phone, url, image_path):
        self.phone = phone
        self.url = url
        self.image_path = image_path

    def create_qrcode(self):
        # 生成二维码
        qr = qrcode.QRCode(
            version=5,  # 一个整数，范围为1到40，表示二维码的大小（最小值是1，是个12×12的矩阵）如果想让程序自动生成，将值设置为 None 并使用 fit=True 参数即可。
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # 二维码的纠错范围，可以选择4个常量：
            box_size=8,  # 每个点（方块）中的像素个数
            border=4  # 二维码距图像外围边框距离，默认为4，而且相关规定最小为4
        )
        qr.add_data(self.url+'?'+self.phone)
        qr.make(fit=True)
        img = qr.make_image()
        img.save(self.image_path)
        img.show()

    def read_qrcode(self):
        # 读取二维码信息
        if not os.path.exists(self.image_path):
            raise FileExistsError(self.image_path)
        return decode(Image.open(self.image_path))

if __name__ == '__main__':
    phone = '18086829907'
    url = 'http://127.0.0.1:5000'
    image_path = 'baidu.png'
    myQRcode = MyQRcode(phone, url, image_path)
    myQRcode.create_qrcode()
    print(myQRcode.read_qrcode())






