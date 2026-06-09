# Hướng Dẫn Tích Hợp Dịch Vụ Captcha (Integration Guide)

Tài liệu này hướng dẫn cách tích hợp hệ thống Captcha SaaS của chúng ta vào bất kỳ ứng dụng web thực tế nào (bao gồm cả các dự án PHP, Python, Node.js, ASP.NET,...).

Hệ thống Captcha hoạt động theo cơ chế **xác thực 2 bước** (tương tự Google reCAPTCHA hoặc hCaptcha) để đảm bảo tính bảo mật tuyệt đối, tránh rò rỉ khóa bí mật (`SecretKey`).

---

## 1. Quy Trình Hoạt Động Tổng Quan (Workflow)

```text
[ Trình Duyệt Khách ]             [ Website Backend ]            [ C# Captcha SaaS ]
        |                                 |                             |
        |---- 1. Lấy Captcha (SiteKey)---------------------------------->|
        |<--- 2. Trả về ChallengeID & Ảnh --|                             |
        |                                 |                             |
        |-- 3. Gửi Form + Đáp án -------->|                             |
        |   (ChallengeID, UserResponse)   |                             |
        |                                 |-- 4. Xác thực ------------->|
        |                                 |  (SecretKey, ChallengeID)   |
        |                                 |<-- 5. Trả về success ------|
        |<-- 6. Kết quả Form <------------|
```

---

## 2. Bước 1: Khởi Tạo Cấu Hình & Lấy Khóa

Mỗi Website tích hợp cần đăng ký trên Portal của Captcha SaaS để lấy cặp khóa:
1. **`SiteKey` (Khóa công khai - Public Key):** Nhúng vào mã nguồn Frontend (HTML/JS) để yêu cầu hiển thị ảnh captcha.
2. **`SecretKey` (Khóa bí mật - Private Key):** Chỉ lưu ở mã nguồn Backend. Tuyệt đối **không** được để lộ ở phía Client.

---

## 3. Bước 2: Tích Hợp Phía Client (Frontend)

Tại Form của bạn (ví dụ: Form Đăng nhập hoặc Đăng ký), thêm một container hiển thị ảnh captcha và ô nhập dữ liệu.

### Mã HTML/JS mẫu:

```html
<form id="login-form" action="/login" method="POST">
    <!-- Các trường nhập liệu thông thường -->
    <div class="form-group">
        <input type="text" name="username" placeholder="Tên đăng nhập" required>
        <input type="password" name="password" placeholder="Mật khẩu" required>
    </div>

    <!-- KHU VỰC NHÚNG CAPTCHA WIDGET -->
    <div class="captcha-widget" style="margin: 20px 0;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <!-- Ảnh captcha hiển thị -->
            <img id="captcha-img" src="" alt="Captcha Image" style="border: 1px solid #ccc; border-radius: 8px; width: 200px; height: 60px;">
            <!-- Nút đổi captcha -->
            <button type="button" id="btn-refresh-captcha" style="padding: 8px 12px; cursor: pointer;">Đổi mã</button>
        </div>
        
        <!-- Input để người dùng nhập -->
        <input type="text" id="captcha-input" name="captcha_response" placeholder="Nhập 4 ký tự" maxlength="4" required style="width: 200px; padding: 8px; text-transform: uppercase;">
        
        <!-- Input ẩn để lưu Challenge ID -->
        <input type="hidden" id="captcha-challenge-id" name="captcha_challenge_id">
    </div>

    <button type="submit">Đăng Nhập</button>
</form>

<script>
    const SAAS_URL = "http://localhost:5097"; // Thay bằng URL chạy thực tế của Captcha SaaS
    const SITE_KEY = "sitekey_YOUR_PUBLIC_SITE_KEY"; // Thay bằng SiteKey của bạn

    // Hàm gọi API lấy ảnh captcha mới
    async function loadNewCaptcha() {
        try {
            const response = await fetch(`${SAAS_URL}/api/v1/captcha/challenge?siteKey=${SITE_KEY}`);
            const data = await response.json();
            
            if (data.success) {
                // Hiển thị ảnh Base64
                document.getElementById('captcha-img').src = data.image;
                // Lưu lại ChallengeID vào trường ẩn để submit lên Backend
                document.getElementById('captcha-challenge-id').value = data.challengeId;
                // Reset ô nhập liệu
                document.getElementById('captcha-input').value = '';
            } else {
                console.error("Lỗi sinh captcha:", data.error);
            }
        } catch (error) {
            console.error("Không kết nối được đến server Captcha:", error);
        }
    }

    // Tải captcha khi trang load xong
    document.addEventListener("DOMContentLoaded", loadNewCaptcha);
    // Tải captcha mới khi click nút refresh
    document.getElementById("btn-refresh-captcha").addEventListener("click", loadNewCaptcha);
</script>
```

---

## 4. Bước 3: Xác Thực Phía Server (Backend)

Khi người dùng submit form, Backend của website bạn sẽ nhận được các thông tin:
* Dữ liệu form chính (`username`, `password`)
* `captcha_challenge_id` (ChallengeId ẩn dưới frontend)
* `captcha_response` (Chuỗi 4 ký tự người dùng gõ)

Trước khi thực hiện xử lý đăng nhập, Backend của bạn **phải** thực hiện một request HTTP POST (Server-to-Server) đến Captcha SaaS để xác thực:

### API Endpoint Xác Thực:
* **URL:** `http://YOUR_SAAS_URL/api/v1/captcha/verify`
* **Method:** `POST`
* **Content-Type:** `application/json`

### Body Request (JSON):
```json
{
  "secretKey": "secretkey_YOUR_PRIVATE_SECRET_KEY",
  "challengeId": "DỮ_LIỆU_captcha_challenge_id_SUBMIT",
  "response": "DỮ_LIỆU_captcha_response_SUBMIT"
}
```

### Ví dụ triển khai Backend (Node.js/Express):

```javascript
app.post('/login', async (req, res) => {
    const { username, password, captcha_challenge_id, captcha_response } = req.body;

    // 1. Gửi request verify sang Captcha SaaS
    try {
        const verifyRes = await fetch("http://localhost:5097/api/v1/captcha/verify", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                secretKey: "secretkey_YOUR_PRIVATE_SECRET_KEY", // Lưu an toàn ở biến môi trường .env
                challengeId: captcha_challenge_id,
                response: captcha_response
            })
        });

        const verifyData = await verifyRes.json();

        // 2. Kiểm tra kết quả
        if (!verifyData.success) {
            // Xác thực captcha thất bại
            return res.status(400).send("Mã xác thực Captcha không chính xác hoặc đã hết hạn!");
        }
    } catch (error) {
        return res.status(500).send("Lỗi kết nối đến server xác thực Captcha.");
    }

    // 3. Tiến hành xử lý đăng nhập thông thường nếu Captcha đúng
    const user = await db.validateUser(username, password);
    if (user) {
        res.send("Đăng nhập thành công!");
    } else {
        res.send("Sai tài khoản hoặc mật khẩu!");
    }
});
```

---

## 5. Các Nguyên Tắc Bảo Mật Cần Tuân Thủ (Security Best Practices)

1. **Một lần sử dụng (One-time consumption):** Mỗi một `ChallengeId` chỉ được gọi xác thực đúng 1 lần duy nhất. Cho dù kết quả trả về là `success` hay `fail`, hệ thống SaaS sẽ hủy trạng thái `Pending` của challenge đó ngay lập tức để chặn các cuộc tấn công brute-force mò đáp án hoặc replay-attack.
2. **Thời gian hết hạn (Expiration time):** Captcha được sinh ra mặc định chỉ có hiệu lực trong **3 phút**. Nếu người dùng để trang treo quá lâu và gửi form, API sẽ báo hết hạn và yêu cầu nạp lại captcha mới.
3. **Tuyệt đối bảo mật SecretKey:** Không bao giờ đưa `SecretKey` vào mã nguồn client (Javascript, Mobile App). Mọi quá trình xác thực `/verify` phải được chạy từ mã server của bạn.
