import qrcode
import os
from pyzbar.pyzbar import decode
from PIL import Image

# # 参数
url = 'https://www.liangyu.online/programming_academy/user/getConnect'
path = 'myQRCode.png'

# 生成二维码
qr = qrcode.QRCode(
    version=5,  # 一个整数，范围为1到40，表示二维码的大小（最小值是1，是个12×12的矩阵）如果想让程序自动生成，将值设置为 None 并使用 fit=True 参数即可。
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # 二维码的纠错范围，可以选择4个常量：
    box_size=8, # 每个点（方块）中的像素个数
    border=4  # 二维码距图像外围边框距离，默认为4，而且相关规定最小为4
)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image()
img.save(path)
img.show()

# 读取二维码信息
def decode_qr_code(code_img_path):
    if not os.path.exists(code_img_path):
        raise FileExistsError(code_img_path)
    return decode(Image.open(code_img_path))
print(decode_qr_code(path))