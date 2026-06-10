# SaaS Captcha Service (saas-captcha)

Dự án này là dịch vụ SaaS giả lập cung cấp giải pháp sinh và xác thực captcha thời gian thực. Dự án hỗ trợ cả 3 phiên bản captcha nhằm mục đích phục vụ nghiên cứu và đánh giá bảo mật, bao gồm: ảnh tĩnh văn bản nhiễu (V1), mảnh ghép trượt tích hợp xác thực hành vi kéo slider (V2) và Checkbox phân tích hành vi ngầm kết hợp lưới chọn ảnh dự phòng (V3).

Dự án được phát triển bằng ngôn ngữ **C#** trên nền tảng **.NET 9** sử dụng kiến trúc phân tầng (Clean Architecture), SQL Server, Entity Framework Core và SkiaSharp để sinh ảnh/vẽ ảnh.

---

## 🛠️ Tính Năng Chính

### 1. Phiên Bản V1: Text Captcha (Văn bản nhiễu)
*   **Bộ Sinh Ảnh SkiaSharp:** Vẽ ngẫu nhiên **đúng 4 ký tự**, xoay nghiêng ngẫu nhiên (-15 đến +15 độ), đổi kích cỡ (32px-38px) trên từng ký tự và chèn điểm tròn nhiễu cùng đường cong Bezier chéo cắt ngang nét chữ.
*   **API Endpoints:**
    *   `GET /api/v1/captcha/challenge?siteKey=X`: Lấy thử thách captcha mới.
    *   `POST /api/v1/captcha/verify`: Gửi đáp án chữ để xác thực.
*   **Giao diện thử nghiệm:** [http://localhost:5097/index_v1.html](http://localhost:5097/index_v1.html).

### 2. Phiên Bản V2: Slider Puzzle Captcha (Mảnh ghép trượt)
*   **Bộ Sinh Ảnh SkiaSharp:** Tự động nạp ảnh nền phong cảnh ngẫu nhiên, khoét lỗ khuyết tối mờ và cắt mảnh ghép trượt viền sáng răng cưa có dạng puzzle khớp nhau hoàn hảo.
*   **Phân tích hành vi trượt:** API xác thực kiểm tra độ sai lệch vị trí trượt cuối cùng ($\le 3px$) kết hợp phân tích quỹ đạo kéo chuột (tổng thời gian kéo, độ rung lắc trục Y và biến thiên gia tốc) để phát hiện và chặn đứng các script trượt đều hoặc trượt thẳng.
*   **API Endpoints:**
    *   `GET /api/v2/captcha/challenge?siteKey=X`: Trả về ảnh nền khuyết, ảnh mảnh ghép trượt và cao độ `YOffset`.
    *   `POST /api/v2/captcha/verify`: Gửi lên tọa độ trượt `xOffset` và danh sách điểm chuyển động `trajectory: [{x, y, t}]` để xác thực.
*   **Giao diện thử nghiệm:** [http://localhost:5097/index_v2.html](http://localhost:5097/index_v2.html).

### 3. Phiên Bản V3: Behavioral Checkbox + Lưới ảnh dự phòng
*   **Chấm điểm hành vi ngầm:** Khi client tích chọn checkbox, client gửi lên telemetry chuyển động chuột, bàn phím và vân tay trình duyệt. Server phân tích tốc độ gõ phím, độ thẳng quỹ đạo chuột, và các cờ tự động hóa (webdriver, headless) để chấm điểm con người (Score từ 0.0 đến 1.0). Nếu Score < 0.7, server sẽ yêu cầu giải thử thách lưới ảnh.
*   **Lưới chọn ảnh dự phòng 3x3**: Sinh ngẫu nhiên lưới 3x3 ảnh trộn lẫn giữa danh mục đích (Xe hơi, Chó, Mèo, Cây cối) và các ảnh nhiễu khác. Người dùng phải chọn đúng các ô ảnh tương ứng.
*   **API Endpoints:**
    *   `POST /api/v3/captcha/verify-behavior`: Gửi dữ liệu telemetry hành vi của client để nhận điểm số và thử thách lưới ảnh nếu phát hiện bot hoặc bất thường.
    *   `POST /api/v3/captcha/verify-image`: Gửi danh sách index ảnh đã chọn để xác thực.
    *   `POST /api/v3/captcha/verify`: Endpoint xác thực chung.
*   **Giao diện thử nghiệm:** [http://localhost:5097/index_v3.html](http://localhost:5097/index_v3.html).

### 4. Bộ Phục Vụ Huấn Luyện AI (V1)
*   `GET /api/v1/dataset/generate?count=X`: Tự động sinh hàng loạt `X` ảnh captcha lưu trữ cục bộ vào cơ sở dữ liệu và đĩa cứng phục vụ huấn luyện.
*   `GET /api/v1/dataset/export`: Đóng gói toàn bộ tập dữ liệu thành một file ZIP duy nhất chứa thư mục ảnh và file nhãn `dataset.csv` để chuyển sang PyTorch Solver.

---

## 📂 Cấu Trúc Dự Án C#
*   **`src/CaptchaSaaS.Core/`**: Định nghĩa thực thể dữ liệu (`User`, `Website`, `CaptchaChallenge`, `BehavioralTelemetry`), enum loại captcha, và các lớp hợp đồng (Interfaces).
*   **`src/CaptchaSaaS.Infrastructure/`**: 
    *   Cấu hình DbContext kết nối SQL Server và quản lý thực thi Migrations.
    *   Lớp xử lý nghiệp vụ sinh ảnh V1, V2 bằng SkiaSharp và sinh lưới ảnh V3.
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

### 5. Định tuyến Route
- **Swagger API Documentation:** [http://localhost:5097/swagger](http://localhost:5097/swagger) (Đường dẫn gốc `/` tự động chuyển hướng về đây).
- **Giao diện Demo V1 (Text):** [http://localhost:5097/index_v1.html](http://localhost:5097/index_v1.html)
- **Giao diện Demo V2 (Slider):** [http://localhost:5097/index_v2.html](http://localhost:5097/index_v2.html)
- **Giao diện Demo V3 (Checkbox):** [http://localhost:5097/index_v3.html](http://localhost:5097/index_v3.html)
