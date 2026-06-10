import cv2
import numpy as np
import random
import math

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

def generate_human_trajectory(target_x):
    """
    Sinh quỹ đạo trượt chuột mô phỏng hành vi của con người (Human-like Trajectory):
    - Có thời gian kéo tự nhiên (1000ms - 1500ms)
    - Có gia tốc tăng tốc lúc đầu và giảm tốc lúc gần đích (Hàm nội suy Smoothstep)
    - Có độ rung động lệch nhẹ theo trục Y
    - Có điểm overshoot nhẹ (kéo quá đà) và kéo lùi lại để khớp.
    """
    trajectory = []
    
    # Thiết lập tổng thời gian kéo ngẫu nhiên khoảng 900ms - 1400ms
    total_time = random.randint(900, 1400)
    
    # Số bước lấy mẫu (tần số lấy mẫu khoảng 12ms/điểm)
    steps = random.randint(45, 65)
    
    # Điểm xuất phát ban đầu
    trajectory.append({"x": 0.0, "y": 0.0, "t": 0})
    
    # Biên độ lệch Y ngẫu nhiên từ 1.5 đến 3.5px
    y_amplitude = random.uniform(1.5, 3.5)
    
    for i in range(1, steps + 1):
        ratio = i / steps
        
        # Hàm nội suy Smoothstep tạo gia tốc phi tuyến (nhanh ở giữa, chậm hai đầu)
        ease_ratio = 3 * (ratio ** 2) - 2 * (ratio ** 3)
        
        # Thêm nhiễu ngẫu nhiên nhẹ vào gia tốc kéo
        ease_ratio += random.uniform(-0.015, 0.015)
        ease_ratio = max(0.0, min(1.0, ease_ratio))
        
        # Tính toán tọa độ X tạm thời
        x = target_x * ease_ratio
        
        # Tạo overshoot (kéo quá đà khoảng 1.5 - 2.5px khi đạt 88% - 94% hành trình)
        if ratio > 0.88 and ratio < 0.94:
            x += random.uniform(1.2, 2.5)
            
        # Tính toán tọa độ Y (Wobble hình sin + nhiễu ngẫu nhiên nhẹ)
        y = y_amplitude * math.sin(ratio * math.pi * 2) + random.uniform(-0.4, 0.4)
        
        # Tính toán timestamp (ms)
        t = int(total_time * ratio)
        
        trajectory.append({
            "x": round(float(x), 2),
            "y": round(float(y), 2),
            "t": t
        })
        
    # Đảm bảo điểm cuối cùng khớp chính xác tọa độ đích
    trajectory[-1] = {
        "x": float(target_x),
        "y": round(random.uniform(-0.2, 0.2), 2),
        "t": total_time
    }
    
    return trajectory
