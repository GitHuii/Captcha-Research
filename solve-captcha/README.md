# Captcha AI Solver (solve-captcha)

Dự án này sử dụng mô hình học sâu **PyTorch (ResNet18 Multi-Head Classification)** để nhận diện và giải tự động các mã Captcha dạng văn bản nhiễu được sinh ra từ hệ thống C# SaaS.

---

## ⚙️ Hướng dẫn cài đặt cục bộ (Local Setup)

Đảm bảo bạn đã cài đặt Python 3.10+ trên máy tính của mình.

1. **Khởi tạo môi trường ảo `.venv` và kích hoạt:**
   * **Windows:**
     ```bash
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

## 📊 Bước 1: Chuẩn bị dữ liệu (Dataset Setup)

1. Mở trình duyệt và truy cập trang Demo của C# SaaS: `http://localhost:5097/index.html` (hoặc cổng chạy thực tế của bạn).
2. Thiết lập cấu hình Demo để kết nối API.
3. Sinh 4.000 captcha bằng cách gọi API của SaaS qua Swagger hoặc Postman:
   `GET http://localhost:5097/api/v1/dataset/generate?count=4000`
4. Xuất và tải file ZIP về máy bằng cách truy cập:
   `GET http://localhost:5097/api/v1/dataset/export`
5. Sao chép file `captcha_dataset.zip` tải về được vào thư mục `solve-captcha/`.
6. Chạy script để tự động giải nén và chia tập dữ liệu thành **3.000 ảnh Train** và **1.000 ảnh Test**:
   ```bash
   python split_dataset.py --zip captcha_dataset.zip
   ```
   *(Dữ liệu phân chia sẽ được lưu trữ tự động trong thư mục `data/`)*

---

## 🚀 Bước 2: Huấn luyện mô hình AI (Train Model)

Chạy lệnh dưới đây để bắt đầu quá trình huấn luyện:
```bash
python src/train.py --epochs 15 --batch_size 64 --lr 0.001
```
* **Tham số:**
  * `--epochs`: Số lượt huấn luyện (mặc định: 15).
  * `--batch_size`: Kích thước lô dữ liệu (mặc định: 64).
  * `--lr`: Tốc độ học (mặc định: 0.001).
* **Kết quả:**
  * Trọng số mô hình tốt nhất được lưu tại: `model/captcha_model.pth`.
  * Danh sách bảng ký tự lưu tại: `model/alphabet.json`.
  * Đồ thị Loss & Accuracy lưu tại: `model/training_curves.png`.

*Mẹo: Nếu máy tính không có GPU và bạn muốn huấn luyện nhanh, hãy sử dụng file **`train_colab.ipynb`** trên Google Colab.*

---

## 🔮 Bước 3: Dự đoán ảnh captcha đơn lẻ (Inference)

Nếu muốn kiểm tra mô hình dự đoán thử trên một ảnh bất kỳ, hãy chạy:
```bash
python src/predict.py --image "đường_dẫn_đến_ảnh.png"
```

---

## 🎮 Bước 4: Demo Tích Hợp Tự Động (Auto Solve Demo)

Đây là kịch bản chạy thử nghiệm tích hợp tự động kết nối trực tiếp với server C# SaaS đang hoạt động:
1. Đảm bảo ứng dụng C# SaaS đang chạy (`dotnet run`).
2. Chạy lệnh:
   ```bash
   python src/auto_solve_demo.py --api_url http://localhost:5097
   ```
3. **Kịch bản chạy:**
   * Script Python tự động đăng ký demo trên C# SaaS để lấy SiteKey/SecretKey (nếu chưa có).
   * Lấy thử thách captcha mới từ C# SaaS.
   * Chuyển đổi ảnh nhận được và đưa vào mô hình AI để giải.
   * Gửi kết quả giải của AI lên API `/verify` của C# SaaS.
   * In ra màn hình kết quả phản hồi của server xem AI giải Đúng hay Sai.
   * Chạy liên tiếp 5 lần để thống kê tỷ lệ giải thành công của AI.

---

## 🎨 Bước 5: Giao Diện Web Dự Đoán Trực Quan (Web App AI Captcha Solver)

Nếu muốn trải nghiệm một giao diện đồ họa kéo thả trực quan để thử nghiệm mô hình AI:
1. Đảm bảo bạn đã sao chép `captcha_model.pth` và `alphabet.json` vào thư mục `model/`.
2. Khởi chạy Web Server cục bộ:
   ```bash
   python src/web_app.py
   ```
3. Mở trình duyệt truy cập: **[http://localhost:5001](http://localhost:5001)**.
4. **Tính năng chính:**
   * Kéo thả hoặc click để tải lên ảnh Captcha bất kỳ từ máy tính.
   * Giao diện Glassmorphism mờ ảo hiện đại cùng hiệu ứng quét ảnh động.
   * Hiển thị kết quả dự đoán của AI dạng hoạt họa sinh động.
   * Tích hợp thanh lịch sử giải lưu ở bộ nhớ trình duyệt (`localStorage`) hiển thị kèm hình ảnh thu nhỏ.

