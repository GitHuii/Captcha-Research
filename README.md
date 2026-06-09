# Captcha Research Project (Dự Án Nghiên Cứu & Đánh Giá Captcha)

Dự án này là một hệ thống thử nghiệm đầy đủ (End-to-End) dùng để nghiên cứu, sinh và đánh giá mức độ bảo mật của hệ thống Captcha dạng văn bản nhiễu bằng Trí tuệ Nhân tạo (AI). 

Hệ thống được chia làm hai phần chính:
1. **`saas-captcha/` (C# .NET 9)**: Dịch vụ SaaS cung cấp API sinh ảnh Captcha nhiễu phức tạp và xác thực kết quả.
2. **`solve-captcha/` (Python PyTorch)**: Mô hình học sâu AI (ResNet18 Multi-Head) dùng để giải mã các Captcha từ SaaS và giao diện Web App tải ảnh giải Captcha trực quan.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
Captcha-Research/
│
├── saas-captcha/              # Dự án C# SaaS Captcha Service
│   ├── src/
│   │   ├── CaptchaSaaS.Core/          # Domain Entities & Interfaces
│   │   ├── CaptchaSaaS.Infrastructure/# Cấu hình DB & Bộ sinh ảnh SkiaSharp
│   │   └── CaptchaSaaS.Api/           # Web API Endpoints & Giao diện Demo
│   ├── CaptchaSaaS.sln        # Solution của Visual Studio
│   └── README.md              # Hướng dẫn chi tiết cho C# SaaS
│
├── solve-captcha/             # Dự án Python AI Solver
│   ├── src/
│   │   ├── dataset.py         # Bộ nạp dữ liệu PyTorch DataLoader
│   │   ├── model.py           # Kiến trúc ResNet18 Multi-Head CNN
│   │   ├── train.py           # Script huấn luyện mạng nơ-ron
│   │   ├── predict.py         # Script nhận diện ảnh đơn lẻ
│   │   ├── auto_solve_demo.py # Script kiểm thử tích hợp tự động giải
│   │   ├── web_app.py         # Web App cục bộ tải ảnh giải Captcha
│   │   └── index.html         # Giao diện Web App Glassmorphism
│   ├── train_colab.ipynb      # Jupyter Notebook chạy huấn luyện trên Google Colab
│   ├── requirements.txt       # Danh sách thư viện Python cần cài
│   └── README.md              # Hướng dẫn chi tiết cho AI Solver
│
└── .gitignore                 # File cấu hình bỏ qua Git cho cả 2 project
```

---

## 🚀 Quy Trình Thực Hiện Nghiên Cứu (Quickstart)

Để chạy thử nghiệm toàn bộ hệ thống từ sinh dữ liệu, huấn luyện AI, đến giải captcha, hãy thực hiện theo các bước sau:

### Bước 1: Khởi chạy C# SaaS & Sinh Dataset
1. Di chuyển vào thư mục `saas-captcha` và đọc hướng dẫn trong [saas-captcha/README.md](file:///c:/Users/ADMIN/Desktop/Captcha-Research/saas-captcha/README.md).
2. Khởi chạy Web API:
   ```bash
   dotnet run --project src/CaptchaSaaS.Api
   ```
3. Truy cập giao diện Demo tại: `http://localhost:5097/index.html`.
4. Gọi API sinh 4.000 ảnh Captcha huấn luyện bằng cách truy cập Swagger hoặc gọi HTTP GET:
   `http://localhost:5097/api/v1/dataset/generate?count=4000`
5. Tải file ZIP chứa dataset về máy:
   `http://localhost:5097/api/v1/dataset/export`
6. Sao chép file `captcha_dataset.zip` vừa tải về vào thư mục `solve-captcha/`.

### Bước 2: Huấn luyện Mô hình AI (Local hoặc Google Colab)
Bạn có thể huấn luyện mô hình trực tiếp trên máy tính cá nhân hoặc sử dụng GPU miễn phí của Google Colab:
* **Phương án Google Colab (Khuyên dùng - Nhanh hơn):**
  1. Upload file notebook `train_colab.ipynb` lên Google Colab.
  2. Nén mã nguồn `solve-captcha` thành `solve-captcha.zip` (không nén thư mục `.venv` để giảm dung lượng).
  3. Upload `solve-captcha.zip` và `captcha_dataset.zip` lên Colab và chạy tuần tự các cell hướng dẫn.
  4. Sau khi hoàn thành, tải 2 file kết quả `captcha_model.pth` và `alphabet.json` về máy tính, đặt vào thư mục `solve-captcha/model/`.
* **Phương án Huấn luyện Local:**
  1. Di chuyển vào thư mục `solve-captcha` và xem hướng dẫn chi tiết tại [solve-captcha/README.md](file:///c:/Users/ADMIN/Desktop/Captcha-Research/solve-captcha/README.md).
  2. Tạo môi trường ảo, cài đặt thư viện từ `requirements.txt`.
  3. Chạy phân chia tập dữ liệu: `python split_dataset.py --zip captcha_dataset.zip`.
  4. Chạy huấn luyện: `python src/train.py --epochs 15`.

### Bước 3: Đánh giá & Sử dụng Kết quả AI

#### Cách A: Chạy Demo giải tự động tích hợp
Với server C# SaaS đang chạy ở cổng `5097`, chạy lệnh sau trong thư mục `solve-captcha` để kiểm tra AI giải Captcha tự động thời gian thực:
```bash
python src/auto_solve_demo.py --api_url http://localhost:5097
```

#### Cách B: Sử dụng giao diện Web tương tác trực quan
Khởi chạy Web App cục bộ để tự tay kéo thả và kiểm thử từng ảnh Captcha:
```bash
python src/web_app.py
```
Truy cập trình duyệt tại: **[http://localhost:5001](http://localhost:5001)** để trải nghiệm giao diện tải ảnh giải captcha trực quan.
