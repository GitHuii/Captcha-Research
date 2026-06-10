# SaaS Captcha Service (saas-captcha)

Dự án này là dịch vụ SaaS giả lập cung cấp giải pháp xác thực bảo mật thông qua ảnh Captcha dạng văn bản nhiễu phức tạp (V1) và mảnh ghép trượt (V2). Dự án được phát triển bằng ngôn ngữ **C#** trên nền tảng **.NET 9** sử dụng kiến trúc phân tầng (Clean Architecture), SQL Server, Entity Framework Core và SkiaSharp để sinh ảnh.

---

## 🛠️ Tính Năng Chính

### 1. Phiên Bản V1: Text Captcha (Văn bản nhiễu)
*   **Bộ Sinh Ảnh SkiaSharp:** Vẽ ngẫu nhiên **đúng 4 ký tự**, xoay nghiêng ngẫu nhiên (-15 đến +15 độ), đổi kích cỡ (32px-38px) trên từng ký tự và chèn điểm tròn nhiễu cùng đường cong Bezier chéo cắt ngang nét chữ.
*   **API Endpoints:**
    *   **`GET /api/v1/captcha/challenge?siteKey=X`**: Lấy thử thách captcha mới (trả về ID thử thách và ảnh dưới dạng chuỗi Base64).
    *   **`POST /api/v1/captcha/verify`**: Gửi đáp án chữ để xác thực.
*   **Giao diện thử nghiệm:** [http://localhost:5097/index.html](http://localhost:5097/index.html).

### 2. Phiên Bản V2: Slider Puzzle Captcha (Mảnh ghép trượt)
*   **Bộ Sinh Ảnh SkiaSharp:** Tự động nạp ảnh nền phong cảnh ngẫu nhiên trong thư mục `wwwroot/assets/backgrounds/`, khoét lỗ khuyết tối mờ và cắt mảnh ghép trượt viền sáng răng cưa có dạng puzzle khớp nhau hoàn hảo.
*   **Phân tích hành vi chống Bot:** API xác thực kiểm tra độ sai lệch vị trí trượt cuối cùng ($\le 4px$) kết hợp phân tích quỹ đạo kéo chuột (đánh giá tổng thời gian kéo, độ rung lắc trục Y và biến thiên gia tốc) để phát hiện và chặn đứng script giả lập.
*   **API Endpoints:**
    *   **`GET /api/v2/captcha/challenge?siteKey=X`**: Trả về ảnh nền khuyết, ảnh mảnh ghép trượt và cao độ `YOffset`.
    *   **`POST /api/v2/captcha/verify`**: Gửi lên tọa độ trượt `xOffset` và danh sách điểm chuyển động `trajectory: [{x, y, t}]` để xác thực.
*   **Giao diện thử nghiệm:** [http://localhost:5097/index_v2.html](http://localhost:5097/index_v2.html).

### 3. Bộ Phục Vụ Huấn Luyện AI (V1)
*   **`GET /api/v1/dataset/generate?count=X`**: Tự động sinh hàng loạt `X` ảnh captcha lưu trữ cục bộ vào cơ sở dữ liệu và đĩa cứng phục vụ huấn luyện.
*   **`GET /api/v1/dataset/export`**: Đóng gói toàn bộ tập dữ liệu thành một file ZIP duy nhất chứa thư mục ảnh và file nhãn `dataset.csv` để chuyển sang PyTorch Solver.

---

## 📂 Cấu Trúc Dự Án C#
*   **`src/CaptchaSaaS.Core/`**: Định nghĩa thực thể dữ liệu (`User`, `Website`, `CaptchaChallenge`), enum loại captcha, và các lớp hợp đồng (Interfaces).
*   **`src/CaptchaSaaS.Infrastructure/`**: 
    *   Cấu hình DbContext kết nối SQL Server và quản lý thực thi Migrations.
    *   Lớp xử lý nghiệp vụ sinh ảnh V1 và V2 bằng SkiaSharp.
    *   Lưu trữ file ảnh trên đĩa cứng local.
*   **`src/CaptchaSaaS.Api/`**: Phục vụ các API Endpoints, tích hợp Swagger UI, định tuyến tài nguyên tĩnh và giao diện web demo.

---

## ⚙️ Hướng Dẫn Cài Đặt & Khởi Chạy Local

### 1. Yêu cầu hệ thống
- Cài đặt [.NET 9 SDK](https://dotnet.microsoft.com/download/dotnet/9.0)
- SQL Server (LocalDB mặc định được hỗ trợ sẵn)

### 2. Cấu hình chuỗi kết nối Database
Chuỗi kết nối được thiết lập mặc định trong [saas-captcha/src/CaptchaSaaS.Api/appsettings.json](file:///c:/Users/ADMIN/Desktop/Captcha-Research/saas-captcha/src/CaptchaSaaS.Api/appsettings.json):
```json
"ConnectionStrings": {
  "DefaultConnection": "Server=(localdb)\\mssqllocaldb;Database=CaptchaSaaS;Trusted_Connection=True;MultipleActiveResultSets=true"
}
```

### 3. Cập nhật Cơ sở dữ liệu (Database Migrations)
Mở terminal tại thư mục `saas-captcha` và chạy:
```powershell
dotnet ef database update --project src/CaptchaSaaS.Infrastructure --startup-project src/CaptchaSaaS.Api
```

### 4. Khởi chạy Server Web API
```powershell
dotnet run --project src/CaptchaSaaS.Api
```
*Mặc định ứng dụng sẽ khởi chạy tại cổng HTTP: **`http://localhost:5097`***

### 5. Kiểm tra kết quả
- **Swagger API Documentation:** [http://localhost:5097/swagger](http://localhost:5097/swagger)
- **Giao diện Demo V1 (Text):** [http://localhost:5097/index.html](http://localhost:5097/index.html)
- **Giao diện Demo V2 (Slider):** [http://localhost:5097/index_v2.html](http://localhost:5097/index_v2.html)
