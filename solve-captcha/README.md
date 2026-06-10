# Captcha AI & CV Solver (solve-captcha)

Dự án này chứa hệ thống giải mã captcha tự động bằng Python, phục vụ nghiên cứu và đánh giá bảo mật của các cơ chế captcha tĩnh lẫn động. Dự án được cấu trúc khoa học thành 3 phiên bản độc lập tương ứng với các giải pháp trên SaaS:

- **`src/v1/` (AI Text Solver):** Sử dụng mạng nơ-ron sâu học máy PyTorch (CRNN/CNN Multi-Head) để giải mã văn bản tĩnh nhiễu phức tạp.
- **`src/v2/` (OpenCV Slider Solver - Đã tách file):** Định vị tọa độ khuyết và giả lập di chuột sinh học kéo mảnh ghép trượt vượt qua bộ lọc.
- **`src/v3/` (AI Behavioral Checkbox Solver - Đã tách file):** Mô phỏng hành vi di chuột Bezier + gõ phím trễ ngẫu nhiên ngầm để vượt qua kiểm tra hành vi, đồng thời giải lưới ảnh 3x3 bằng mô hình MobileNetV3 pretrained.

---

## ⚙️ Hướng dẫn cài đặt cục bộ (Local Setup)

Đảm bảo bạn đã cài đặt Python 3.10+ trên máy tính.

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
1. Tải file ZIP dataset chứa các captcha mẫu sinh từ C# SaaS về máy.
2. Sao chép tệp `captcha_dataset.zip` vào thư mục `solve-captcha/`.
3. Phân tách tập dữ liệu thành Train và Test:
   ```powershell
   .\.venv\Scripts\python src/v1/split_dataset.py --zip captcha_dataset.zip
   ```

### Bước 2: Huấn luyện mô hình AI (Train Model)
```powershell
.\.venv\Scripts\python src/v1/train.py --epochs 15 --batch_size 64 --lr 0.001
```
*   **Kết quả:** Trọng số tốt nhất được lưu tại `model/captcha_model.pth`, danh sách ký tự lưu tại `model/alphabet.json`.

### Bước 3: Dự đoán ảnh đơn lẻ
```powershell
.\.venv\Scripts\python src/v1/predict.py --image "duong_dan_anh.png"
```

### Bước 4: Chạy Demo giải tự động tích hợp (V1)
```powershell
.\.venv\Scripts\python src/v1/auto_solve_demo.py --api_url http://localhost:5097
```

### Bước 5: Mở Web App trực quan của AI V1
```powershell
.\.venv\Scripts\python src/v1/web_app.py
```
Truy cập: **[http://localhost:5001](http://localhost:5001)** để trải nghiệm giao diện kéo thả giải captcha văn bản.

---

## 🧩 Hướng Dẫn Sử Dụng Phiên Bản V2 (Slider Puzzle Captcha)

Phiên bản V2 được phân tách thành các module khoa học:
- **`trajectory.py`**: Chứa thuật toán sinh chuyển động trượt chuột sinh học của con người (bao gồm vận tốc kéo biến thiên, độ rung lắc hình sin nhẹ, điểm trượt quá đà overshoot và giật lùi chỉnh sửa).
- **`solver.py`**: Sử dụng OpenCV Canny Edge và Template Matching để so khớp vị trí mảnh ghép trên ảnh nền chính nhằm trích xuất khoảng cách trượt $X$.
- **`auto_solve_demo.py`**: Script chạy thử nghiệm tự động tích hợp gửi request lên server API để trượt giải và nhận phản hồi.

### Chạy thử nghiệm tự động:
```powershell
.\.venv\Scripts\python src/v2/auto_solve_demo.py --api_url http://localhost:5097
```
*(Hệ thống sẽ chạy liên tiếp 5 lượt trượt giải và hiển thị kết quả thành công/thất bại).*

---

## 🧠 Hướng Dẫn Sử Dụng Phiên Bản V3 (Behavioral Checkbox + Fallback Grid)

Phiên bản V3 được phân tách thành các module khoa học:
- **`telemetry.py`**: Trình giả lập hành vi sinh học của người thật: sinh quỹ đạo di chuyển chuột ngẫu nhiên dựa trên **Đường cong Bezier bậc 3** đi qua các vùng input trước khi click checkbox, giả lập gõ phím trễ ngẫu nhiên mô phỏng tốc độ gõ phím thật.
- **`classifier.py`**: Bộ tải mô hình học sâu **MobileNetV3 (Large Pretrained)**. Tự động tải 9 ảnh trong thử thách dự phòng của server, phân loại bằng AI và tự động ánh xạ nhãn ImageNet sang 4 danh mục đích (chó, mèo, xe, cây).
- **`auto_solve_demo.py`**: Script chạy thử nghiệm tích hợp thực hiện hai kịch bản:
  1. *Kịch bản 1 (Naive Bot)*: Thao tác trơn tuột không chuột, không delay $\rightarrow$ Bị server chặn và yêu cầu fallback.
  2. *Kịch bản 2 (Stealth Bot + AI Grid Bypass)*: Gửi hành vi di chuột Bezier tinh vi kết hợp gọi mô hình MobileNetV3 tự động giải lưới ảnh để vượt qua captcha.

### Chạy thử nghiệm tự động:
```powershell
.\.venv\Scripts\python src/v3/auto_solve_demo.py
```
