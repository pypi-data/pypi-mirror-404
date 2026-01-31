from PIL import Image
import pytesseract
import cv2
import numpy as np
import os

def preprocess_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法加载图片: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 11, 2)
    cv2.imwrite("processed_image.png", thresh)  # 保存预处理图片
    return thresh

def recognize_text(image_path):
    try:
        processed_image = preprocess_image(image_path)
        pil_image = Image.fromarray(processed_image)
        pytesseract.pytesseract.tesseract_cmd = r'D:\TesseractOCR\tesseract.exe'
        text = pytesseract.image_to_string(pil_image, lang='chi_sim+eng', config='--oem 3 --psm 6')
        if not text.strip():
            print("警告: 未识别到任何文字")
        return text.strip()
    except Exception as e:
        return f"错误: {str(e)}"

def main():
    image_path = "imageRecognition.png"
    print(f"检查图片路径: {os.path.exists(image_path)}")
    result = recognize_text(image_path)
    print("识别的文字：")
    print(result)

if __name__ == "__main__":
    main()