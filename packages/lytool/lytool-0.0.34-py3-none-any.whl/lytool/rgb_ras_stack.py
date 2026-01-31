import numpy as np
import cv2
# ue5灰度图片优化：将三张灰度图片分别存放到rgb通道，导入ue5的材质编辑器后，就能通过rgb通道获得三张灰度图片的数组

rough_path = input('请输入roughness图片的文件名')
ao_path = input('请输入ao图片的文件名')
spec_path = input('请输入spec图片的文件名')

rough_array = cv2.imread(rough_path, 0)
ao_array = cv2.imread(ao_path, 0)
spec_array = cv2.imread(spec_path, 0)
rgb_ras = np.stack((ao_array, spec_array, rough_array), axis=0).T
cv2.imwrite('rgb_ras.jpg', rgb_ras)