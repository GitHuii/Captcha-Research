# SaaS Captcha Service (saas-captcha)

Dự án này là dịch vụ SaaS giả lập cung cấp giải pháp xác thực bảo mật thông qua ảnh Captcha dạng văn bản nhiễu phức tạp. Dự án được phát triển bằng ngôn ngữ **C#** trên nền tảng **.NET 9** sử dụng kiến trúc phân tầng (Clean Architecture), SQL Server, Entity Framework Core và SkiaSharp để sinh ảnh.

---

## 🛠️ Tính Năng Chính
1. **Bộ Sinh Ảnh SkiaSharp Captcha nhiễu phức tạp:**
   - Vẽ ngẫu nhiên **đúng 4 ký tự** (chữ cái và chữ số).
   - Áp dụng các phép biến hình: Xoay nghiêng ngẫu nhiên (-15 đến +15 độ), đổi kích cỡ (32px-38px) trên từng ký tự.
   - Vẽ chèn các yếu tố nhiễu: 120-180 điểm tròn nhỏ li ti và 2-4 đường cong Bezier chéo cắt ngang nét chữ nhằm đánh lừa các công cụ OCR cơ bản.
2. **API Portal Đăng Ký Đối Tác:**
   - API đăng ký tài khoản User và đăng ký Website tích hợp.
   - Tự động sinh khóa bảo mật cặp đối tác: **`SiteKey`** (phục vụ client-side widget) và **`SecretKey`** (phục vụ server-side verify).
3. **API Widget Captcha:**
   - **`GET /api/v1/captcha/challenge`**: Lấy thử thách captcha mới (trả về ID thử thách và ảnh dưới dạng chuỗi Base64).
   - **`POST /api/v1/captcha/verify`**: Gửi đáp án từ client lên kèm `SecretKey` để đối chiếu và xác thực.
4. **Bộ Phục Vụ Huấn Luyện AI (AI Training Engine):**
   - **`GET /api/v1/dataset/generate?count=X`**: Tự động sinh hàng loạt `X` ảnh captcha lưu trữ cục bộ vào cơ sở dữ liệu và đĩa cứng phục vụ huấn luyện.
   - **`GET /api/v1/dataset/export`**: Đóng gói toàn bộ tập dữ liệu thành một file ZIP duy nhất chứa thư mục ảnh và file nhãn `dataset.csv` để chuyển sang PyTorch Solver.
5. **Giao Diện Thử Nghiệm Widget Demo:**
   - Nằm tại thư mục `wwwroot/index.html`, cung cấp giao diện Glassmorphism tuyệt đẹp cho phép người dùng cấu hình địa chỉ API, tải và gõ thử captcha thực tế.

---

## 📂 Cấu Trúc Dự Án C#
* **`src/CaptchaSaaS.Core/`**: Định nghĩa các thực thể dữ liệu (`User`, `Website`, `CaptchaChallenge`) và các lớp hợp đồng (Interfaces).
* **`src/CaptchaSaaS.Infrastructure/`**: 
  * Cấu hình DbContext kết nối SQL Server và quản lý thực thi Migrations.
  * Lớp xử lý nghiệp vụ sinh ảnh và gây nhiễu bằng SkiaSharp.
  * Lưu trữ file ảnh trên đĩa cứng local.
* **`src/CaptchaSaaS.Api/`**: Phục vụ các API Endpoints, tích hợp Swagger UI, định tuyến tài nguyên tĩnh và giao diện web demo.

---

## ⚙️ Hướng Dẫn Cài Đặt & Khởi Chạy Local

### 1. Yêu cầu hệ thống
- Cài đặt [.NET 9 SDK](https://dotnet.microsoft.com/download/dotnet/9.0)
- SQL Server (LocalDB mặc định được hỗ trợ sẵn hoặc SQL Server Express/Enterprise)

### 2. Cấu hình chuỗi kết nối Database
Chuỗi kết nối được thiết lập mặc định trong [saas-captcha/src/CaptchaSaaS.Api/appsettings.json](file:///c:/Users/ADMIN/Desktop/Captcha-Research/saas-captcha/src/CaptchaSaaS.Api/appsettings.json):
```json
"ConnectionStrings": {
  "DefaultConnection": "Server=(localdb)\\mssqllocaldb;Database=CaptchaSaaS;Trusted_Connection=True;MultipleActiveResultSets=true"
}
```
*Bạn có thể chỉnh sửa chuỗi này cho phù hợp với máy của bạn nếu cần.*

### 3. Cập nhật Cơ sở dữ liệu (Database Migrations)
Để áp dụng cấu hình bảng vào SQL Server của bạn, mở terminal tại thư mục `saas-captcha` và chạy:
```powershell
dotnet ef database update --project src/CaptchaSaaS.Infrastructure --startup-project src/CaptchaSaaS.Api
```

### 4. Khởi chạy Server Web API
Chạy lệnh sau từ thư mục `saas-captcha` để bắt đầu:
```powershell
dotnet run --project src/CaptchaSaaS.Api
```
*Mặc định ứng dụng sẽ khởi chạy tại cổng HTTP: **`http://localhost:5097`***

### 5. Kiểm tra kết quả
- **Swagger API Documentation:** [http://localhost:5097/swagger](http://localhost:5097/swagger) (giúp bạn gọi thử các API trực tiếp).
- **Giao diện Demo Widget:** [http://localhost:5097/index.html](http://localhost:5097/index.html) (trang thử nghiệm giao diện captcha).
