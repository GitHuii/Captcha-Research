import os
import json
import base64
import argparse
import requests
from solver import solve_slider_captcha, generate_human_trajectory

def main():
    parser = argparse.ArgumentParser(description="Chạy Demo tích hợp tự động giải Captcha V2: Nhận Slider Captcha -> Giải bằng OpenCV -> Sinh quỹ đạo kéo chuột -> Gửi xác thực.")
    parser.add_argument("--api_url", type=str, default="http://localhost:5097", 
                        help="Đường dẫn đến C# Web API SaaS (mặc định: http://localhost:5097)")
    args = parser.parse_args()

    api_url = args.api_url.rstrip('/')
    keys_file = "demo_keys.json"
    site_key = ""
    secret_key = ""

    # 1. Đọc hoặc tự động khởi tạo cặp khóa SiteKey/SecretKey thử nghiệm
    # Xem xét ở thư mục gốc của solver-captcha hoặc thư mục mẹ (nếu chạy từ root)
    if os.path.exists(keys_file):
        with open(keys_file, 'r') as f:
            keys = json.load(f)
            site_key = keys.get("siteKey")
            secret_key = keys.get("secretKey")
            print("🔑 Đã nạp khóa cấu hình từ demo_keys.json")
    else:
        # Kiểm tra thử ở thư mục mẹ
        parent_keys_path = os.path.join("..", keys_file)
        if os.path.exists(parent_keys_path):
            with open(parent_keys_path, 'r') as f:
                keys = json.load(f)
                site_key = keys.get("siteKey")
                secret_key = keys.get("secretKey")
                print("🔑 Đã nạp khóa cấu hình từ ../demo_keys.json")
        else:
            print("⚙️ Không tìm thấy demo_keys.json. Đang đăng ký tự động trên C# SaaS...")
            try:
                # Đăng ký user
                user_res = requests.post(f"{api_url}/api/v1/portal/users", json={
                    "email": f"python_ai_v2_agent_{os.getpid()}@test.com",
                    "password": "PythonAgentPassword123"
                })
                user_res.raise_for_status()
                user_data = user_res.json()

                # Đăng ký website
                site_res = requests.post(f"{api_url}/api/v1/portal/websites", json={
                    "userId": user_data["id"],
                    "domain": "localhost"
                })
                site_res.raise_for_status()
                site_data = site_res.json()

                site_key = site_data["siteKey"]
                secret_key = site_data["secretKey"]

                # Lưu lại
                with open(keys_file, 'w') as f:
                    json.dump({"siteKey": site_key, "secretKey": secret_key}, f)
                print("🚀 Đăng ký thành công! Đã lưu khóa vào demo_keys.json")
            except Exception as e:
                print(f"❌ Không thể kết nối hoặc đăng ký trên C# SaaS tại: {api_url}")
                print(f"Chi tiết lỗi: {e}")
                print("Hãy chắc chắn rằng ứng dụng C# SaaS Web API đang chạy bằng lệnh 'dotnet run'!")
                return

    # 2. Chạy Demo giải Captcha V2 tự động 5 lần liên tục
    print(f"\n🎮 BẮT ĐẦU CHẠY THỬ NGHIỆM TỰ ĐỘNG GIẢI CAPTCHA V2 (5 lượt)...")
    temp_bg_path = "temp_v2_bg.png"
    temp_block_path = "temp_v2_block.png"
    
    success_count = 0
    total_count = 5

    for i in range(total_count):
        print(f"\n--- Lượt giải #{i+1} ---")
        try:
            # Bước A: Lấy thử thách captcha trượt từ C# SaaS
            challenge_res = requests.get(f"{api_url}/api/v2/captcha/challenge?siteKey={site_key}")
            challenge_res.raise_for_status()
            challenge_data = challenge_res.json()

            challenge_id = challenge_data["challengeId"]
            base64_bg = challenge_data["bgImage"]
            base64_block = challenge_data["blockImage"]

            # Bước B: Giải mã ảnh Base64 và lưu file tạm thời
            if "," in base64_bg:
                base64_bg = base64_bg.split(",")[1]
            if "," in base64_block:
                base64_block = base64_block.split(",")[1]
            
            bg_data = base64.b64decode(base64_bg)
            with open(temp_bg_path, "wb") as f:
                f.write(bg_data)

            block_data = base64.b64decode(base64_block)
            with open(temp_block_path, "wb") as f:
                f.write(block_data)

            # Bước C: Sử dụng OpenCV Edge Template Matching để định vị X
            predicted_x = solve_slider_captcha(temp_bg_path, temp_block_path)
            print(f"👁️  OpenCV định vị vị trí khuyết X: {predicted_x}px")

            # Bước D: Sinh quỹ đạo trượt chuột sinh học của con người
            human_trajectory = generate_human_trajectory(predicted_x)
            print(f"✍️  Đã sinh quỹ đạo trượt chuột: {len(human_trajectory)} điểm di chuyển trong {human_trajectory[-1]['t']}ms")

            # Bước E: Gửi đáp án tọa độ + quỹ đạo lên API verify của C# SaaS
            verify_res = requests.post(f"{api_url}/api/v2/captcha/verify", json={
                "secretKey": secret_key,
                "challengeId": challenge_id,
                "xOffset": predicted_x,
                "trajectory": human_trajectory
            })
            verify_res.raise_for_status()
            verify_data = verify_res.json()

            # Bước F: Đánh giá kết quả phản hồi
            if verify_data.get("success"):
                print("🟢 THÀNH CÔNG: C# SaaS phản hồi: Captcha CHÍNH XÁC & Chấp nhận hành vi con người!")
                success_count += 1
            else:
                print(f"🔴 THẤT BẠI: C# SaaS phản hồi: Từ chối xác thực! (Lỗi: {verify_data.get('error')})")

        except Exception as e:
            print(f"❌ Xảy ra lỗi ở lượt #{i+1}: {e}")
        finally:
            # Dọn dẹp ảnh tạm thời
            if os.path.exists(temp_bg_path):
                os.remove(temp_bg_path)
            if os.path.exists(temp_block_path):
                os.remove(temp_block_path)

    # 3. In thống kê kết quả
    print(f"\n📈 KẾT QUẢ CUỐI CÙNG CAPTCHA V2:")
    print(f"   AI giải đúng: {success_count}/{total_count} captchas (Tỷ lệ: {success_count/total_count * 100:.1f}%)")

if __name__ == "__main__":
    main()
