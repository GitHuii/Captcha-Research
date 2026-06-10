# Captcha Research Project (Dự Án Nghiên Cứu & Đánh Giá Captcha)

Dự án này là một hệ thống thử nghiệm đầy đủ (End-to-End) dùng để nghiên cứu, sinh và đánh giá mức độ bảo mật của các hệ thống Captcha thông qua Trí tuệ Nhân tạo (AI) và Thị giác Máy tính. 

Hệ thống được chia làm hai phần chính:
1. **`saas-captcha/` (C# .NET 9)**: Dịch vụ SaaS cung cấp API sinh ảnh Captcha dạng văn bản nhiễu phức tạp (V1) và dạng mảnh ghép trượt (V2), đồng thời xác thực kết quả kèm phân tích hành vi trượt chuột chống Bot.
2. **`solve-captcha/` (Python)**: Bộ giải mã captcha tự động gồm mô hình PyTorch ResNet18 Multi-Head để giải Captcha V1 (Text) và giải thuật OpenCV Edge-based Template Matching kết hợp sinh hành trình trượt chuột sinh học để giải Captcha V2 (Slider).

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
Captcha-Research/
│
├── saas-captcha/              # Dự án C# SaaS Captcha Service
│   ├── src/
│   │   ├── CaptchaSaaS.Core/          # Domain Entities, Interfaces & Trajectory Validator
│   │   ├── CaptchaSaaS.Infrastructure/# Bộ sinh ảnh SkiaSharp (V1 & V2) & Cấu hình DB
│   │   └── CaptchaSaaS.Api/           # Web API Endpoints & Giao diện Demo (V1 & V2)
│   ├── CaptchaSaaS.sln        # Solution của Visual Studio
│   └── README.md              # Hướng dẫn chi tiết cho C# SaaS
│
├── solve-captcha/             # Dự án Python AI & CV Solver
│   ├── src/
│   │   ├── v1/                # Bộ Giải Captcha V1 (AI Text)
│   │   │   ├── dataset.py     # DataLoader PyTorch
│   │   │   ├── model.py       # Kiến trúc ResNet18 Multi-Head CNN
│   │   │   ├── train.py       # Script huấn luyện nơ-ron
│   │   │   ├── predict.py     # Script dự đoán ảnh đơn lẻ
│   │   │   ├── web_app.py     # Web App cục bộ giải captcha kéo thả
│   │   │   ├── index.html     # Giao diện Web App AI V1
│   │   │   ├── split_dataset.py# Script chia tập dữ liệu Train/Test
│   │   │   ├── train_colab.ipynb# Notebook Colab huấn luyện mô hình
│   │   │   └── auto_solve_demo.py# Script chạy thử nghiệm tự động giải V1
│   │   │
│   │   └── v2/                # Bộ Giải Captcha V2 (Slider Puzzle)
│   │       ├── solver.py      # Định vị OpenCV Canny + Sinh quỹ đạo chuột
│   │       └── auto_solve_demo.py# Script chạy thử nghiệm tự động giải V2
│   │
│   ├── requirements.txt       # Danh sách thư viện Python cần cài
│   └── README.md              # Hướng dẫn chi tiết cho AI & CV Solver
│
└── README.md                  # Tài liệu hướng dẫn tổng quan dự án (File này)
```

---

## 🚀 Quy Trình Thực Hiện Nghiên Cứu (Quickstart)

### Bước 1: Khởi chạy C# SaaS & Cập Nhật DB
1. Di chuyển vào thư mục `saas-captcha` và cập nhật cơ sở dữ liệu:
   ```powershell
   dotnet ef database update --project src/CaptchaSaaS.Infrastructure --startup-project src/CaptchaSaaS.Api
   ```
2. Khởi chạy Web API:
   ```powershell
   dotnet run --project src/CaptchaSaaS.Api
   ```
   *Server sẽ chạy tại cổng mặc định:* `http://localhost:5097`

---

### Bước 2: Thử Nghiệm & Đánh Giá Captcha V1 (Văn Bản Nhiễu)

#### A. Trải nghiệm trực quan:
*   Mở trình duyệt truy cập: **[http://localhost:5097/index.html](http://localhost:5097/index.html)**.

#### B. Huấn luyện mô hình AI tự giải:
1. Gọi API sinh 4.000 ảnh Captcha V1 huấn luyện:
   `http://localhost:5097/api/v1/dataset/generate?count=4000`
2. Tải file ZIP chứa dataset về máy:
   `http://localhost:5097/api/v1/dataset/export`
3. Copy file `captcha_dataset.zip` vừa tải về vào thư mục `solve-captcha/`.
4. Kích hoạt môi trường ảo Python trong `solve-captcha` và phân chia tập dữ liệu:
   ```powershell
   .venv\Scripts\python src/v1/split_dataset.py --zip captcha_dataset.zip
   ```
5. Chạy huấn luyện mô hình ResNet18:
   ```powershell
   .venv\Scripts\python src/v1/train.py --epochs 15
   ```
6. Chạy thử nghiệm giải tự động thời gian thực kết nối với SaaS:
   ```powershell
   .venv\Scripts\python src/v1/auto_solve_demo.py
   ```

---

### Bước 3: Thử Nghiệm & Đánh Giá Captcha V2 (Mảnh Ghép Trượt)

#### A. Trải nghiệm trực quan (có tính năng kiểm thử Bot):
*   Mở trình duyệt truy cập: **[http://localhost:5097/index_v2.html](http://localhost:5097/index_v2.html)**.
*   Bạn có thể kéo slider thủ công hoặc tích chọn **"Giả lập Bot tấn công"** để xem server phân tích hành vi và ngăn chặn bot kéo tự động như thế nào.

#### B. Chạy OpenCV Solver tự động giải V2:
Chạy lệnh sau trong thư mục `solve-captcha` để kích hoạt CV Solver tự động xác định vị trí mảnh ghép bằng OpenCV và sinh hành trình trượt chuột sinh học để giải mã vượt qua bộ lọc của SaaS:
```powershell
.venv\Scripts\python src/v2/auto_solve_demo.py
```
*(Hệ thống sẽ chạy liên tiếp 5 lượt giải và thống kê tỷ lệ vượt qua thành công).*
