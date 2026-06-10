import os
import json
import base64
import argparse
import requests
from predict import predict

# File: solve-captcha/src/auto_solve_demo.py

def main():
    parser = argparse.ArgumentParser(description="Chạy Demo tích hợp tự động: Nhận Captcha từ C# SaaS -> Giải bằng AI -> Gửi xác thực.")
    parser.add_argument("--api_url", type=str, default="http://localhost:5097", 
                        help="Đường dẫn đến C# Web API SaaS (mặc định: http://localhost:5097)")
    parser.add_argument("--model_path", type=str, default="model/v1/captcha_model.pth", 
                        help="Đường dẫn đến file model (.pth)")
    parser.add_argument("--alphabet_path", type=str, default="model/v1/alphabet.json", 
                        help="Đường dẫn đến file alphabet.json")
    args = parser.parse_args()

    api_url = args.api_url.rstrip('/')
    keys_file = "demo_keys.json"
    site_key = ""
    secret_key = ""

    # 1. Đảm bảo đã huấn luyện AI trước khi chạy
    if not os.path.exists(args.model_path):
        print(f"❌ Lỗi: Chưa tìm thấy file mô hình tại {args.model_path}.")
        print("Vui lòng sinh dữ liệu từ C# SaaS và chạy huấn luyện mạng nơ-ron bằng lệnh 'python src/train.py' trước!")
        return

    # 2. Đọc hoặc tự động khởi tạo cặp khóa SiteKey/SecretKey thử nghiệm
    if os.path.exists(keys_file):
        with open(keys_file, 'r') as f:
            keys = json.load(f)
            site_key = keys.get("siteKey")
            secret_key = keys.get("secretKey")
            print("🔑 Đã nạp khóa cấu hình sẵn từ demo_keys.json")
    else:
        print("⚙️ Không tìm thấy demo_keys.json. Đang đăng ký tự động trên C# SaaS...")
        try:
            # Đăng ký user
            user_res = requests.post(f"{api_url}/api/v1/portal/users", json={
                "email": f"python_ai_agent_{os.getpid()}@test.com",
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

            # Lưu lại để lần sau không phải đăng ký lại
            with open(keys_file, 'w') as f:
                json.dump({"siteKey": site_key, "secretKey": secret_key}, f)
            print("🚀 Đăng ký thành công! Đã lưu khóa vào demo_keys.json")
        except Exception as e:
            print(f"❌ Không thể kết nối hoặc đăng ký trên C# SaaS tại: {api_url}")
            print(f"Chi tiết lỗi: {e}")
            print("Hãy chắc chắn rằng ứng dụng C# SaaS Web API đang chạy bằng lệnh 'dotnet run'!")
            return

    # 3. Chạy Demo giải Captcha tự động 5 lần liên tục
    print(f"\n🎮 BẮT ĐẦU CHẠY THỬ NGHIỆM GIẢI TỰ ĐỘNG (5 lượt)...")
    temp_img_path = "temp_challenge_to_solve.png"
    
    success_count = 0
    total_count = 5

    for i in range(total_count):
        print(f"\n--- Lượt giải #{i+1} ---")
        try:
            # Bước A: Lấy thử thách captcha từ C# SaaS
            challenge_res = requests.get(f"{api_url}/api/v1/captcha/challenge?siteKey={site_key}")
            challenge_res.raise_for_status()
            challenge_data = challenge_res.json()

            challenge_id = challenge_data["challengeId"]
            base64_image = challenge_data["image"]

            # Bước B: Giải mã ảnh Base64 và lưu file tạm thời
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]
            
            img_data = base64.b64decode(base64_image)
            with open(temp_img_path, "wb") as f:
                f.write(img_data)

            # Bước C: Đưa ảnh vào mô hình AI để nhận diện đáp án
            predicted_text = predict(temp_img_path, args.model_path, args.alphabet_path)
            print(f"🤖 AI nhận diện captcha thành: [ {predicted_text} ]")

            # Bước D: Gửi đáp án của AI lên API verify của C# SaaS để xác thực
            verify_res = requests.post(f"{api_url}/api/v1/captcha/verify", json={
                "secretKey": secret_key,
                "challengeId": challenge_id,
                "response": predicted_text
            })
            verify_res.raise_for_status()
            verify_data = verify_res.json()

            # Bước E: Đánh giá kết quả
            if verify_data.get("success"):
                print("🟢 THÀNH CÔNG: C# SaaS phản hồi: Captcha CHÍNH XÁC!")
                success_count += 1
            else:
                print(f"🔴 THẤT BẠI: C# SaaS phản hồi: Captcha SAI! (Lỗi: {verify_data.get('error')})")

        except Exception as e:
            print(f"❌ Xảy ra lỗi ở lượt #{i+1}: {e}")
        finally:
            # Dọn dẹp ảnh tạm thời
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)

    # 4. In thống kê
    print(f"\n📈 KẾT QUẢ CUỐI CÙNG:")
    print(f"   AI giải đúng: {success_count}/{total_count} captchas (Tỷ lệ: {success_count/total_count * 100:.1f}%)")

if __name__ == "__main__":
    main()
