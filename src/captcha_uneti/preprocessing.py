"""
Tiền xử lý ảnh CAPTCHA UNETI: lọc nhiễu đường kẻ xanh và nhị phân hóa.
"""
import cv2
import numpy as np
import random
from PIL import Image


def thresholded_denoise(pil_img, thresh_val=220):
    """
    Lọc nhiễu đường kẻ xanh bằng HSV masking và nhị phân hóa.
    Dùng cho inference (thresh cố định = 220).
    """
    open_cv_image = np.array(pil_img)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    hsv = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    line_mask = (s > 150) & (v < 220)
    open_cv_image[line_mask] = [255, 255, 255]

    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
    rgb_image = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(rgb_image)


def thresholded_denoise_random(pil_img, is_train=True):
    """
    Lọc nhiễu với threshold ngẫu nhiên (190-230) khi train, cố định (220) khi eval.
    Randomized threshold giúp mô hình generalize tốt hơn.
    """
    if is_train:
        thresh_val = random.randint(190, 230)
    else:
        thresh_val = 220
    return thresholded_denoise(pil_img, thresh_val=thresh_val)
