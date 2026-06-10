import os
import time
import random
import requests

from telemetry import simulate_human_trajectory, simulate_human_keystrokes
from classifier import CaptchaV3Solver

# Configs
BASE_URL = "http://localhost:5097"

def main():
    print("=== CAPTCHA V3 RESEARCH AUTOMATED Solver ===")
    
    # 0. Đăng ký thông tin Website Demo
    session = requests.Session()
    
    try:
        # Đăng ký User mới
        email = f"bot_v3_{random.randint(1000, 9999)}@ai.com"
        user_res = session.post(f"{BASE_URL}/api/v1/portal/users", json={
            "email": email,
            "password": "Password123"
        }, timeout=5).json()
        user_id = user_res["id"]
        
        # Đăng ký Website để lấy SiteKey & SecretKey
        site_res = session.post(f"{BASE_URL}/api/v1/portal/websites", json={
            "userId": user_id,
            "domain": "localhost"
        }, timeout=5).json()
        
        site_key = site_res["siteKey"]
        secret_key = site_res["secretKey"]
        print(f"Registered Website successfully. \nSiteKey: {site_key}\nSecretKey: {secret_key}\n")
    except Exception as e:
        print(f"SaaS API is not running or error connecting: {e}")
        print("Please make sure CaptchaSaaS.Api C# service is running at http://localhost:5097")
        return

    # Khởi tạo AI Solver
    solver = CaptchaV3Solver()

    # ==========================================
    # KỊCH BẢN 1: NAIVE BOT (Thao tác thô sơ -> Bị phát hiện)
    # ==========================================
    print("\n--- RUNNING SCENARIO 1: NAIVE BOT ---")
    naive_telemetry = {
        "mouseActions": [],  # Không di chuyển chuột
        "keyActions": [      # Gõ phím cực nhanh cách nhau 1ms
            {"key": "a", "type": "keydown", "t": 1},
            {"key": "a", "type": "keyup", "t": 2},
            {"key": "b", "type": "keydown", "t": 3},
            {"key": "b", "type": "keyup", "t": 4}
        ],
        "clickActions": [{"x": 250, "y": 480, "target": "submit_btn", "t": 10}],
        "scrollActions": [],
        "fingerprint": {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HeadlessChrome/114.0.0.0",
            "screenWidth": 1920,
            "screenHeight": 1080,
            "webdriver": True,       # Kích hoạt cờ tự động hóa
            "canvasHash": "8ab3cf2",
            "timezoneOffset": -420,
            "languages": "vi-VN,vi",
            "isHeadless": True
        }
    }

    try:
        res = session.post(f"{BASE_URL}/api/v3/captcha/verify-behavior", json={
            "siteKey": site_key,
            "telemetry": naive_telemetry
        }, timeout=5).json()

        print(f"API Response: Success={res['success']}, Score={res['score']}, RequireFallback={res.get('requireFallback', False)}")
        if res.get('requireFallback'):
            print(f"Blocked Reasons: {res.get('reasons')}")
    except Exception as e:
        print(f"Failed calling verify-behavior: {e}")


    # ==========================================
    # KỊCH BẢN 2: STEALTH BOT BYPASSING BEHAVIOR + AI IMAGE GRID SOLVER
    # ==========================================
    print("\n--- RUNNING SCENARIO 2: STEALTH BOT + AI GRID BYPASS ---")
    
    # 2.1 Tạo hành trình chuột sinh học (Bezier) di chuyển quanh form rồi mới nhấn nút
    # Di chuyển từ (100, 100) -> (300, 250) (Nhập User) -> (300, 320) (Nhập Pass) -> (350, 480) (Bấm Submit)
    mouse_traj = []
    mouse_traj.extend(simulate_human_trajectory((100, 100), (300, 250), duration_ms=250, steps=25))
    
    # Giả lập gõ phím user
    key_actions = simulate_human_keystrokes("admin@captcha-research.vn")
    
    # Di chuyển từ ô nhập user sang ô nhập pass
    last_t = mouse_traj[-1]["t"]
    traj_pass = simulate_human_trajectory((300, 250), (300, 320), duration_ms=180, steps=15)
    for p in traj_pass:
        p["t"] += last_t + 100 # cộng độ trễ
    mouse_traj.extend(traj_pass)
    
    # Giả lập gõ phím password
    key_pass = simulate_human_keystrokes("SuperSecretPassword123")
    last_key_t = key_actions[-1]["t"]
    for k in key_pass:
        k["t"] += last_key_t + 200
    key_actions.extend(key_pass)

    # Di chuyển chuột đến nút submit
    last_t = mouse_traj[-1]["t"]
    traj_submit = simulate_human_trajectory((300, 320), (350, 480), duration_ms=220, steps=20)
    for p in traj_submit:
        p["t"] += last_t + 150
    mouse_traj.extend(traj_submit)

    click_time = mouse_traj[-1]["t"] + 50
    click_actions = [{
        "x": 350,
        "y": 480,
        "target": "btn-form-submit",
        "t": click_time
    }]

    # Tạo cờ vân tay bình thường không có cờ headless để kiểm thử
    # (Để chắc chắn kích hoạt được lưới ảnh V2 để demo bộ giải AI, chúng ta sẽ gửi cờ headless là True
    # nhưng hành vi chuột cực kỳ xịn để xem hệ thống bắt được gì và yêu cầu fallback)
    stealth_telemetry = {
        "mouseActions": mouse_traj,
        "keyActions": key_actions,
        "clickActions": click_actions,
        "scrollActions": [],
        "fingerprint": {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "screenWidth": 1920,
            "screenHeight": 1080,
            "webdriver": False,     # Tắt cờ webdriver
            "canvasHash": "c1f7a0b2",
            "timezoneOffset": -420,
            "languages": "vi-VN,vi,en",
            "isHeadless": True      # Bật cờ headless để cố ý kích hoạt Thử thách Lưới ảnh dự phòng
        }
    }

    try:
        print("Sending stealth behavioral telemetry to Server...")
        res = session.post(f"{BASE_URL}/api/v3/captcha/verify-behavior", json={
            "siteKey": site_key,
            "telemetry": stealth_telemetry
        }, timeout=5).json()

        print(f"Server Evaluation: Success={res['success']}, Score={res['score']}, RequireFallback={res.get('requireFallback', False)}")
        
        if res.get('requireFallback'):
            challenge_id = res['challengeId']
            prompt_text = res['promptText']
            target_category = res['targetCategory']
            images = res['images']
            
            print(f"\n[Fallback Triggered] Target Category: {target_category} ('{prompt_text}')")
            print("Downloading 9 images and running AI inference...")
            
            selected_indices = []
            
            for item in images:
                idx = item['index']
                img_url = item['imageUrl']
                
                # Download ảnh
                img_bytes = solver.download_image(img_url)
                if not img_bytes:
                    print(f"  - Image {idx}: Download failed.")
                    continue
                
                # Nhận diện ảnh bằng AI
                mapped_cat, raw_label, conf = solver.classify_image(img_bytes)
                print(f"  - Image {idx}: Predicted Class='{raw_label}' (Conf={conf:.2f}) -> Mapped Category='{mapped_cat}'")
                
                if mapped_cat == target_category:
                    print(f"    * MATCH FOUND! Selecting index {idx}.")
                    selected_indices.append(idx)
                    
            print(f"\nFinal AI Selected Indices: {selected_indices}")
            
            # Giải lập quỹ đạo rê chuột click vào các ô ảnh được chọn để bypass cờ hành vi
            # Trong phiên bản demo API, chúng ta sẽ gửi thẳng các index đã chọn lên xác thực
            print("Submitting grid selection solution to Server...")
            verify_res = session.post(f"{BASE_URL}/api/v3/captcha/verify-image", json={
                "secretKey": secret_key,
                "challengeId": challenge_id,
                "selectedIndices": selected_indices
            }, timeout=5).json()
            
            print(f"Verification Result: {verify_res}")
            if verify_res.get('success'):
                print(">>> SUCCESS: AI Solver successfully bypassed Captcha V3!")
            else:
                print(">>> FAILED: Verification failed.", verify_res.get('error'))
        else:
            print("Bypassed directly without fallback challenge!")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Failed running Scenario 2: {e}")

if __name__ == "__main__":
    main()
