import cv2
import numpy as np

def solve_slider_captcha(bg_path, block_path):
    """
    Sử dụng OpenCV Edge-based Template Matching để tìm tọa độ X của lỗ khuyết.
    """
    # 1. Đọc ảnh dưới dạng Grayscale
    bg_img = cv2.imread(bg_path, 0)
    block_img = cv2.imread(block_path, 0)
    
    if bg_img is None or block_img is None:
        raise FileNotFoundError("Không thể đọc file ảnh nền hoặc ảnh mảnh ghép.")

    # 2. Phát hiện đường biên bằng Canny (giúp giữ cấu hình nét cắt răng cưa)
    bg_edges = cv2.Canny(bg_img, 100, 200)
    block_edges = cv2.Canny(block_img, 100, 200)

    # 3. So khớp mẫu (Template Matching) trên ảnh viền nét
    result = cv2.matchTemplate(bg_edges, block_edges, cv2.TM_CCOEFF_NORMED)

    # 4. Tìm điểm có độ tương khớp lớn nhất
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
    # max_loc[0] chính là tọa độ X (cạnh trái mảnh ghép khớp vị trí lỗ khuyết)
    return float(max_loc[0])
