# Captcha AI Solver (solve-captcha)

Dự án này là hệ thống giải captcha tự động, chia làm hai phiên bản độc lập để phục vụ nghiên cứu và đánh giá:
1. **`src/v1/` (AI Text Solver):** Sử dụng mô hình học sâu **PyTorch (ResNet18 Multi-Head)** để giải mã văn bản captcha dạng tĩnh nhiễu phức tạp.
2. **`src/v2/` (OpenCV Slider Solver):** Sử dụng thuật toán xử lý ảnh **OpenCV Canny Edge + Template Matching** để tìm tọa độ lỗ khuyết mảnh ghép trượt, kết hợp bộ sinh quỹ đạo di chuyển chuột mô phỏng hành vi sinh học của con người (vượt qua bộ lọc hành vi).

---

## ⚙️ Hướng dẫn cài đặt cục bộ (Local Setup)

Đảm bảo bạn đã cài đặt Python 3.10+ trên máy tính của mình.

1. **Khởi tạo môi trường ảo `.venv` và kích hoạt:**
   * **Windows:**
     ```powershell
     python -m venv .venv
     .venv\Scripts\activate
     ```
   * **Linux/macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

2. **Cài đặt các thư viện cần thiết:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 📊 Hướng Dẫn Sử Dụng Phiên Bản V1 (AI Text Captcha)

### Bước 1: Chuẩn bị dữ liệu (Dataset Setup)
1. Truy cập trang demo V1 của SaaS: `http://localhost:5097/index.html`.
2. Sinh và tải file zip chứa 4.000 captcha mẫu huấn luyện về máy.
3. Copy file `captcha_dataset.zip` vào thư mục `solve-captcha/`.
4. Giải nén và phân tách dữ liệu thành tập Train (3.000) và Test (1.000):
   ```powershell
   python src/v1/split_dataset.py --zip captcha_dataset.zip
   ```

### Bước 2: Huấn luyện mô hình AI (Train Model)
```powershell
python src/v1/train.py --epochs 15 --batch_size 64 --lr 0.001
```
*   **Kết quả:** Trọng số tốt nhất được lưu tại `model/captcha_model.pth`, danh sách ký tự lưu tại `model/alphabet.json`.

### Bước 3: Dự đoán ảnh đơn lẻ
```powershell
python src/v1/predict.py --image "duong_dan_anh.png"
```

### Bước 4: Chạy Demo giải tự động tích hợp (V1)
```powershell
python src/v1/auto_solve_demo.py --api_url http://localhost:5097
```

### Bước 5: Mở Web App trực quan của AI V1
```powershell
python src/v1/web_app.py
```
Truy cập: **[http://localhost:5001](http://localhost:5001)** để trải nghiệm giao diện kéo thả giải captcha văn bản.

---

## 🚀 Hướng Dẫn Sử Dụng Phiên Bản V2 (Slider Puzzle Captcha)

Phiên bản V2 kết hợp định vị ảnh bằng OpenCV và sinh hành trình trượt chuột sinh học của con người để vượt qua bộ lọc chống Bot của Server.

### Bước 1: Khởi chạy C# SaaS Server
Đảm bảo dự án SaaS API đang chạy (`dotnet run`).

### Bước 2: Chạy Demo giải tự động tích hợp (V2)
```powershell
python src/v2/auto_solve_demo.py --api_url http://localhost:5097
```

*   **Cơ chế hoạt động:**
    1. Python Agent tự động lấy siteKey từ `demo_keys.json`.
    2. Yêu cầu một thử thách mảnh ghép V2 từ server.
    3. Sử dụng OpenCV Canny Edge để tách biên ảnh nền và mảnh ghép, định vị vị trí khuyết $X$.
    4. Sinh hành trình trượt chuột (vận tốc biến thiên Smoothstep, rung lắc nhẹ trục Y, có overshoot) mô phỏng người thật.
    5. Gửi lên `/verify` của server C# và nhận kết quả phản hồi thành công/thất bại.
