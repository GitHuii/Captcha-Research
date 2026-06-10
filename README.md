# Captcha Research Project (Dự Án Nghiên Cứu & Đánh Giá Captcha Toàn Diện)

Dự án này là một hệ thống thử nghiệm đầy đủ (End-to-End) dùng để nghiên cứu, sinh và đánh giá mức độ bảo mật của các giải pháp Captcha khác nhau chống lại Trí tuệ Nhân tạo (AI) và Thị giác Máy tính. Dự án xây dựng 3 phiên bản Captcha từ cơ bản đến phức tạp nhất:
1. **V1 (Text Captcha)**: Nhận dạng ký tự ảnh nhiễu.
2. **V2 (Slider Puzzle Captcha)**: Ghép mảnh hình ảnh tích hợp phân tích hành vi kéo slider.
3. **V3 (Behavioral Checkbox + Fallback Image Grid)**: Tích hợp phân tích hành vi di chuột, gõ phím ngầm (reCAPTCHA v2 style) kết hợp lưới chọn ảnh 3x3 dự phòng giải quyết bằng mạng nơ-ron sâu.

Hệ thống được chia làm hai phần chính:
- **`saas-captcha/` (C# .NET 9)**: Dịch vụ SaaS cung cấp cơ chế sinh và xác thực captcha thời gian thực, quản lý phân tích hành vi người dùng, và cung cấp các giao diện demo UI tối giản (Minimalist Theme).
- **`solve-captcha/` (Python)**: Hệ thống AI/CV Solvers được module hóa khoa học để tự động hóa việc phá giải các cơ chế bảo mật của Captcha nhằm đánh giá độ an toàn.

---

## 📁 Cấu Trúc Thư Mục Hệ Thống

```text
Captcha-Research/
│
├── saas-captcha/                  # C# SaaS Captcha Service (.NET 9)
│   ├── src/
│   │   ├── CaptchaSaaS.Core/          # Entities, Interfaces & Logic nghiệp vụ chính
│   │   │   ├── Entities/
│   │   │   │   ├── CaptchaChallenge.cs   # Lưu trữ thông tin thử thách
│   │   │   │   ├── BehavioralTelemetry.cs# DTO lưu trữ hành vi chuột/phím của Client
│   │   │   │   └── CaptchaType.cs        # Enum các loại captcha (V1, V2, V3)
│   │   │   └── Services/
│   │   │       ├── BehavioralValidator.cs# Thuật toán chấm điểm hành vi sinh học ngầm
│   │   │       └── SliderTrajectoryValidator.cs # Xác thực quỹ đạo kéo slider
│   │   │
│   │   ├── CaptchaSaaS.Infrastructure/# Cấu hình EF Core SQL Server & Sinh ảnh (SkiaSharp)
│   │   │   └── Services/
│   │   │       ├── CaptchaGenerator.cs    # Tạo ảnh chữ nhiễu V1
│   │   │       ├── SliderCaptchaGenerator.cs # Tạo ảnh trượt khuyết răng cưa V2
│   │   │       └── ImageGridGenerator.cs  # Tạo lưới ảnh 3x3 V3 phục vụ fallback
│   │   │
│   │   └── CaptchaSaaS.Api/           # Web API Endpoints & Giao diện Demo
│   │       ├── Controllers/
│   │       │   ├── CaptchaController.cs   # API V1 (Text)
│   │       │   ├── CaptchaV2Controller.cs # API V2 (Slider)
│   │       │   ├── CaptchaV3Controller.cs # API V3 (Behavioral / Image Grid)
│   │       │   └── DatasetController.cs   # Phục vụ sinh xuất dữ liệu huấn luyện V1
│   │       ├── Program.cs             # Cấu hình middleware, định hướng route
│   │       └── wwwroot/               # Tệp tĩnh & Giao diện HTML Minimalist mới
│   │           ├── index_v1.html      # Demo V1 (Text Captcha)
│   │           ├── index_v2.html      # Demo V2 (Slider Captcha)
│   │           ├── index_v3.html      # Demo V3 (Checkbox & Lưới chọn ảnh)
│   │           └── assets/js/
│   │               └── v3-tracker.js  # Script client-side ghi nhận telemetry ngầm
│   │
│   └── CaptchaSaaS.sln            # Solution của Visual Studio
│
├── solve-captcha/                 # Python AI & CV Solver
│   ├── .venv/                     # Môi trường ảo Python
│   ├── requirements.txt           # Thư viện cần thiết (PyTorch, OpenCV, Requests...)
│   └── src/
│       ├── v1/                    # Bộ giải mã Captcha V1 (AI Text)
│       │   ├── dataset.py         # Bộ tải dữ liệu huấn luyện PyTorch
│       │   ├── model.py           # Thiết kế mô hình học sâu CNN Multi-head
│       │   ├── train.py           # Huấn luyện mô hình từ đầu
│       │   ├── predict.py         # Nhận diện một ảnh đơn lẻ
│       │   ├── split_dataset.py   # Chia tập Train/Val/Test
│       │   └── auto_solve_demo.py # Script kiểm thử tự động giải mã V1 với Server
│       │
│       ├── v2/                    # Bộ giải mã Captcha V2 (Slider Puzzle)
│       │   ├── solver.py          # Sử dụng OpenCV định vị lỗ khuyết của mảnh ghép
│       │   ├── trajectory.py      # Sinh quỹ đạo kéo slider sinh học mô phỏng người
│       │   └── auto_solve_demo.py # Script kiểm thử tự động giải mã V2 với Server
│       │
│       └── v3/                    # Bộ giải mã Captcha V3 (Behavioral Checkbox)
│           ├── classifier.py      # Bộ phân loại ảnh 3x3 lưới bằng MobileNetV3 Pretrained
│           ├── telemetry.py       # Bộ mô phỏng hành vi di chuột Bezier + gõ phím trễ ngẫu nhiên
│           └── auto_solve_demo.py # Script kiểm thử tự động giải mã V3 với Server
│
└── README.md                      # Hướng dẫn tổng quan (File này)
```

---

## ⚙️ Quy Tắc Định Tuyến & Giao Diện Của Server C#

Server được thiết kế dựa trên các tiêu chí giao diện sạch sẽ, chuyên nghiệp và tối giản (Minimalist Theme) sử dụng hệ màu **Trắng - Xám - Xanh lam** kết hợp bộ font **Outfit** và **Google Material Icons** thay thế cho các emoji/văn bản thường:

- **Định tuyến Gốc (/)**: Truy cập `http://localhost:5097/` sẽ tự động redirect (mã HTTP 302) về trang tài liệu API Swagger `http://localhost:5097/swagger`.
- **Swagger UI**: Hoạt động trực tiếp tại địa chỉ `http://localhost:5097/swagger`.
- **Giao diện Client Demo**:
  - **V1 (Text)**: `http://localhost:5097/index_v1.html`
  - **V2 (Slider)**: `http://localhost:5097/index_v2.html`
  - **V3 (Checkbox)**: `http://localhost:5097/index_v3.html`

---

## 🚀 Hướng Dẫn Khởi Chạy Nhanh (Quickstart)

### Bước 1: Khởi chạy API Server C# .NET 9
1. Yêu cầu máy cài đặt **SQL Server** và **.NET 9 SDK**.
2. Di chuyển vào thư mục dự án C#:
   ```powershell
   cd saas-captcha
   ```
3. Chạy cập nhật Cơ sở dữ liệu (Entity Framework Core):
   ```powershell
   dotnet ef database update --project src/CaptchaSaaS.Infrastructure --startup-project src/CaptchaSaaS.Api
   ```
4. Chạy dự án API:
   ```powershell
   dotnet run --project src/CaptchaSaaS.Api
   ```
   *Server sẽ khởi chạy tại:* `http://localhost:5097` (có thể truy cập Swagger tại `/swagger` để kiểm tra tài liệu API).

---

### Bước 2: Thiết lập Môi trường ảo Python cho Solver
1. Di chuyển vào thư mục Python:
   ```powershell
   cd ../solve-captcha
   ```
2. Tạo môi trường ảo và cài đặt thư viện cần thiết:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## 🛡️ Chi Tiết Kiểm Thử 3 Phiên Bản Captcha

### 📊 Captcha V1: Văn Bản Nhiễu (Noisy Text)
*   **Cơ chế sinh của Server**: Tạo ảnh chứa 4 ký tự ngẫu nhiên, áp dụng các đường cong nhiễu, điểm ảnh hạt muối tiêu và biến dạng sóng (Wave distortion) bằng SkiaSharp.
*   **Cơ chế giải của AI**: Xây dựng mô hình CNN Multi-head để dự đoán cùng lúc 4 vị trí ký tự.
*   **Kiểm thử tự động**:
    1. Tải bộ dữ liệu huấn luyện mẫu (ví dụ 4000 ảnh) từ endpoint:
       `http://localhost:5097/api/v1/dataset/generate?count=4000`
    2. Xuất và lưu bộ dữ liệu zip: `http://localhost:5097/api/v1/dataset/export`
    3. Trích xuất file `.zip` vào thư mục `solve-captcha/` rồi phân chia tập dữ liệu:
       ```powershell
       .\.venv\Scripts\python src/v1/split_dataset.py --zip captcha_dataset.zip
       ```
    4. Huấn luyện mạng nơ-ron:
       ```powershell
       .\.venv\Scripts\python src/v1/train.py --epochs 15
       ```
    5. Chạy demo tự động giải thời gian thực:
       ```powershell
       .\.venv\Scripts\python src/v1/auto_solve_demo.py
       ```

---

### 🧩 Captcha V2: Mảnh Ghép Trượt (Slider Puzzle)
*   **Cơ chế sinh của Server**: Cắt một mảnh ghép hình răng cưa (Block) ra khỏi ảnh nền tại tọa độ X ngẫu nhiên, tạo bóng đổ khuyết trên ảnh nền chính.
*   **Cơ chế đánh giá của Server**: So sánh sai số tọa độ trượt X (cho phép lệch ±3px), đồng thời phân tích chuỗi tọa độ chuột trượt (trajectory) của client gửi lên:
    - *Từ chối*: Các đường thẳng hoàn hảo (không có độ võng rung lắc tự nhiên của tay người).
    - *Từ chối*: Tốc độ di chuyển kéo đều tắp hoặc thời gian trượt quá nhanh (dưới 300ms).
*   **Cơ chế giải của AI (`src/v2`)**:
    - **`solver.py`**: Sử dụng OpenCV Canny Edge Detection để tìm viền mảnh ghép và viền lỗ khuyết, sau đó dùng thuật toán Template Matching (`matchTemplate`) tìm tọa độ khuyết X chính xác.
    - **`trajectory.py`**: Sử dụng hàm trơn phi tuyến (Smoothstep) để tạo gia tốc biến thiên (nhanh ở giữa, chậm ở đầu và đích), mô phỏng gia tốc sinh học kết hợp rung lắc hình sin nhẹ và kéo quá đà (overshoot) rồi kéo giật lùi về đúng vị trí để đánh lừa thuật toán phát hiện bot.
*   **Kiểm thử tự động**:
    ```powershell
    .\.venv\Scripts\python src/v2/auto_solve_demo.py
    ```

---

### 🧠 Captcha V3: Checkbox Phân Tích Hành Vi & Lưới Ảnh Dự Phòng
*   **Cơ chế đánh giá hành vi ngầm của Server**: Khi người dùng click vào Checkbox *"Tôi không phải là người máy"*, client gửi toàn bộ telemetry hoạt động chuột, bàn phím và vân tay thiết bị lên Server để đánh giá điểm số (Human Score: `0.0` đến `1.0`):
    - Kiểm tra vân tay robot: Các cờ tự động hóa như `navigator.webdriver` bị bật, môi trường không đầu (headless browser).
    - Phân tích chuyển động chuột: Kiểm tra biến thiên vận tốc (Velocity Variance). Nếu chuột đi theo một đường thẳng tuyệt đối hoặc tốc độ không thay đổi $\rightarrow$ Đánh giá Bot.
    - Phân tích gõ phím: Nếu người dùng nhập thông tin đăng nhập với tốc độ tức thì (delay = 0ms hoặc đều tăm tắp) $\rightarrow$ Đánh giá Bot.
    - *Kết quả*: Nếu Score $\ge$ 0.7 $\rightarrow$ Vượt qua trực tiếp (hiện dấu tích xanh `✓`). Ngược lại, kích hoạt cơ chế dự phòng: hiện bảng lưới ảnh 3x3.
*   **Cơ chế lưới ảnh dự phòng**: Server sinh ngẫu nhiên lưới 3x3 ảnh trộn lẫn giữa danh mục mục tiêu (ví dụ: Chó/Mèo/Xe/Cây) và các ảnh nhiễu khác. Người dùng phải chọn đúng các ô ảnh tương ứng.
*   **Cơ chế giải của AI (`src/v3`)**:
    - **`telemetry.py`**: Tạo chuyển động chuột sinh học phức tạp dựa trên thuật toán **Bezier Curve bậc 3** di chuyển tự nhiên từ vị trí xuất phát đi qua các input tài khoản/mật khẩu trước khi tích chọn checkbox, giả lập gõ phím trễ ngẫu nhiên mô phỏng tốc độ gõ của người thật.
    - **`classifier.py`**: Sử dụng mạng nơ-ron học sâu tích chập **MobileNetV3** (Large Pretrained) từ PyTorch. Khi lưới ảnh fallback được mở ra, AI tải 9 ảnh xuống và phân loại trực tiếp. Nhãn ImageNet dự đoán được ánh xạ sang 4 danh mục của hệ thống để đưa ra quyết định chọn chính xác.
*   **Kiểm thử tự động**:
    ```powershell
    .\.venv\Scripts\python src/v3/auto_solve_demo.py
    ```
    *Kịch bản kiểm thử sẽ chạy song song:*
    1. **Naive Bot**: Gửi hành vi thô sơ (bị Server phát hiện lập tức, Score = 0).
    2. **Stealth Bot**: Gửi hành vi giả lập sinh học tinh vi, cố tình kích hoạt cờ Headless để mở lưới ảnh dự phòng $\rightarrow$ Dùng mạng nơ-ron MobileNetV3 tự động giải lưới ảnh để bypass thành công.
