import random
import math

def generate_bezier_point(p0, p1, p2, p3, t):
    """Tính toán điểm tại thời điểm t (0 -> 1) cho đường cong Bezier bậc 3"""
    x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
    y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
    return x, y

def simulate_human_trajectory(start, end, duration_ms=600, steps=80):
    """Sinh quỹ đạo chuột mô phỏng hành vi sinh học của con người"""
    trajectory = []
    
    # Tạo 2 điểm điều khiển ngẫu nhiên để tạo đường cong tự nhiên
    p0 = start
    p3 = end
    
    # Điểm điều khiển p1 và p2 lệch nhẹ so với đường thẳng nối p0 và p3
    mid_x = (p0[0] + p3[0]) / 2
    mid_y = (p0[1] + p3[1]) / 2
    dist = math.sqrt((p3[0] - p0[0])**2 + (p3[1] - p0[1])**2)
    
    offset_dist = dist * random.uniform(0.1, 0.25)
    angle = math.atan2(p3[1] - p0[1], p3[0] - p0[0]) + random.choice([-math.pi/2, math.pi/2])
    
    p1 = (mid_x + offset_dist * math.cos(angle) + random.uniform(-20, 20),
          mid_y + offset_dist * math.sin(angle) + random.uniform(-20, 20))
    p2 = (mid_x + random.uniform(-30, 30), mid_y + random.uniform(-30, 30))
    
    start_time = 0
    t_step = 1.0 / steps
    
    for i in range(steps + 1):
        t = i * t_step
        # Sử dụng hàm Easing (Ease-in-out) để giả lập gia tốc tăng dần rồi giảm dần khi dừng
        t_eased = t * t * (3 - 2 * t)
        
        x, y = generate_bezier_point(p0, p1, p2, p3, t_eased)
        
        # Thêm nhiễu Gaussian cực nhẹ (tay người luôn có độ rung rất nhỏ ~ 0.2px)
        x += random.gauss(0, 0.15)
        y += random.gauss(0, 0.15)
        
        # Thời gian tiến trình trượt
        time_elapsed = int(t * duration_ms)
        trajectory.append({
            "x": round(x, 2),
            "y": round(y, 2),
            "t": time_elapsed
        })
        
    return trajectory

def simulate_human_keystrokes(text):
    key_actions = []
    current_time = 50 # Bắt đầu sau 50ms
    
    for char in text:
        # Bấm phím xuống (KeyDown)
        key_actions.append({
            "key": char,
            "type": "keydown",
            "t": current_time
        })
        
        # Thời gian giữ phím (Key Hold duration) thường từ 40ms - 100ms
        hold_time = random.randint(40, 100)
        current_time += hold_time
        
        # Nhả phím lên (KeyUp)
        key_actions.append({
            "key": char,
            "type": "keyup",
            "t": current_time
        })
        
        # Thời gian chờ trước khi bấm phím tiếp theo (Key Interval) từ 60ms - 180ms
        interval_time = random.randint(60, 180)
        current_time += interval_time
        
    return key_actions
