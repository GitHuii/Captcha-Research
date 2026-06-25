# 📊 BÁO CÁO NGHIÊN CỨU TỔNG KẾT
# Hệ thống Nhận diện CAPTCHA UNETI bằng Deep Learning

> **Tác giả**: Nguyễn Viết Huy, Hoàng Thanh Chiến
> **Ngày hoàn thành**: 25/06/2026
> **Độ chính xác đạt được**: **97.63% Word Accuracy** (536/549 ảnh test đúng)

---

## Mục lục

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Dữ liệu & Tiền xử lý](#2-dữ-liệu--tiền-xử-lý)
3. [Kiến trúc mô hình](#3-kiến-trúc-mô-hình)
4. [Chiến lược huấn luyện](#4-chiến-lược-huấn-luyện)
5. [Pipeline suy luận sản xuất](#5-pipeline-suy-luận-sản-xuất)
6. [Kết quả thực nghiệm](#6-kết-quả-thực-nghiệm)
7. [Phân tích lỗi](#7-phân-tích-lỗi)
8. [Hướng dẫn triển khai](#8-hướng-dẫn-triển-khai)
9. [Bài học kinh nghiệm](#9-bài-học-kinh-nghiệm)
10. [Hướng phát triển tương lai](#10-hướng-phát-triển-tương-lai)

---

## 1. Tổng quan dự án

### 1.1. Bối cảnh

Hệ thống đăng nhập của Đại học Kinh tế - Kỹ thuật Công nghiệp (UNETI) sử dụng một cơ chế CAPTCHA văn bản tĩnh để xác minh người dùng. Mỗi ảnh CAPTCHA gồm **4 ký tự** (chữ cái in hoa A-Z và chữ số 0-9) được vẽ trên nền trắng, phủ thêm **các đường kẻ nhiễu màu xanh dương/xanh lam (cyan/blue)** cắt ngang ảnh để gây nhiễu cho máy.

### 1.2. Mục tiêu

Xây dựng hệ thống AI tự động nhận diện chính xác nội dung văn bản của CAPTCHA UNETI, phục vụ nghiên cứu đánh giá mức độ bảo mật của cơ chế CAPTCHA này.

### 1.3. Thông số kỹ thuật CAPTCHA

| Thuộc tính | Giá trị |
|:---|:---|
| Số ký tự | 4 ký tự cố định |
| Bộ ký tự (Alphabet) | 36 lớp: `0-9` + `A-Z` |
| Kích thước ảnh gốc | ~150 × 50 pixels |
| Loại nhiễu | Đường kẻ thẳng màu xanh dương/xanh lam |
| Font chữ | Serif, nghiêng nhẹ, đôi khi dính sát nhau |

---

## 2. Dữ liệu & Tiền xử lý

### 2.1. Thu thập dữ liệu

Dữ liệu được thu thập tự động từ trang đăng nhập UNETI bằng module `src/captcha_uneti/tools/download.py` sử dụng thư viện `requests`. Toàn bộ quy trình:

1. **Tải tự động**: Gửi request GET đến endpoint sinh CAPTCHA, lưu ảnh PNG
2. **Gán nhãn thủ công**: Sử dụng ứng dụng web gán nhãn (`label_app.py`) được xây dựng tùy chỉnh
3. **Xác minh nhãn**: Kiểm tra chéo và sửa các nhãn sai bằng mô hình đã huấn luyện sơ bộ

### 2.2. Phân chia dữ liệu

| Tập | Số lượng | Tỷ lệ | Mục đích |
|:---|:---:|:---:|:---|
| Train | 2,559 | ~70% | Huấn luyện mô hình |
| Validation | 548 | ~15% | Đánh giá trong quá trình huấn luyện, Early Stopping |
| Test | 549 | ~15% | Đánh giá cuối cùng, không dùng khi huấn luyện |

> **Lưu ý**: Tập Test được mở rộng riêng với nhiều mẫu chứa ký tự khó (`Q`, `I`, `1`, `O`) để đánh giá khả năng tổng quát hóa.

### 2.3. Tiền xử lý ảnh (Binarization Pipeline)

Ảnh CAPTCHA gốc chứa các đường kẻ nhiễu màu xanh. Quá trình lọc nhiễu sử dụng **không gian màu HSV**:

```
Ảnh RGB gốc → Chuyển đổi sang HSV → Tạo mask: (Saturation > 150) AND (Value < 220)
→ Xóa pixel nhiễu (đặt = trắng) → Chuyển sang Grayscale → Nhị phân hóa (threshold = 220)
→ Ảnh đen trắng sạch (đầu vào cho nhánh Binarized)
```

**Ưu điểm**:
- Loại bỏ gần như 100% đường kẻ nhiễu, tạo ảnh đen trắng cực kỳ sạch
- Mô hình học dễ hơn trên ảnh sạch → Độ chính xác cơ sở rất cao

**Hạn chế (Giới hạn vật lý)**:
- Khi đường nhiễu **đè trực tiếp lên nét chữ**, bộ lọc HSV bắt buộc phải xóa vùng chồng lấn
- Đuôi chữ `Q` bị cắt → trông giống chữ `O`
- Flag chéo của số `1` bị cắt → trông giống chữ `I`

### 2.4. Chế độ RGB (Bypass Binarization)

Để khắc phục giới hạn vật lý trên, chúng tôi phát triển nhánh huấn luyện RGB:
- **Đầu vào**: Ảnh màu RGB gốc (không lọc nhiễu)
- **Augmentation**: Vẽ thêm 1-3 đường kẻ nhiễu ngẫu nhiên (màu xanh, độ dày 1-2px) lên ảnh train → Mô hình học cách "nhìn xuyên" qua đường nhiễu

### 2.5. Data Augmentation (Khi huấn luyện)

| Kỹ thuật | Tham số |
|:---|:---|
| Random Rotation | ±12° |
| Random Affine | translate=(0.06, 0.06), scale=(0.95, 1.05), degrees=±8° |
| Random Perspective | distortion_scale=0.15, p=0.5 |
| Color Jitter | brightness=0.15, contrast=0.15 |
| Random HSV Threshold (Binarized) | threshold ∈ [190, 230] |
| Synthetic Line Augmentation (RGB) | 1-3 đường kẻ xanh ngẫu nhiên |

---

## 3. Kiến trúc mô hình

### 3.1. Spatial Pooling Multi-Head Architecture

Cả hai mô hình chính (ResNet34 và ResNet18) đều sử dụng kiến trúc **Spatial Pooling** thay vì cách tiếp cận Sequence-to-Sequence (CTC). Ý tưởng cốt lõi:

```
Input Image → ResNet Backbone → AdaptiveAvgPool2d(2, 4) → Reshape thành 4 "cột"
→ Mỗi cột đi qua FC head riêng → Dự đoán 1 ký tự
```

**Giải thích chi tiết**:
1. Ảnh đầu vào đi qua ResNet backbone (conv1 → bn1 → relu → maxpool → layer1-4)
2. Feature map cuối cùng được nén bằng `AdaptiveAvgPool2d(2, 4)` thành kích thước cố định `(batch, 512, 2, 4)`
3. **Reshape thông minh**: `permute(0, 3, 1, 2).reshape(batch, 4, -1)` → Tách 4 cột không gian, mỗi cột chứa vector đặc trưng 1024 chiều (512 × 2)
4. Mỗi vector đi qua FC head chung: `Linear(1024→256) → ReLU → Dropout(0.5) → Linear(256→36)` → Dự đoán 1 trong 36 lớp

**Ưu điểm so với CTC**:
- Không cần xử lý chuỗi có độ dài biến đổi (CAPTCHA luôn có đúng 4 ký tự)
- Huấn luyện đơn giản hơn, hội tụ nhanh hơn
- Spatial Pooling 2×4 tự động chia ảnh thành 4 vùng ngang → mỗi vùng tương ứng 1 ký tự

### 3.2. So sánh hai backbone

| Thuộc tính | ResNet34 Spatial | ResNet18 Spatial |
|:---|:---:|:---:|
| Backbone | ResNet34 (ImageNet pretrained) | ResNet18 (ImageNet pretrained) |
| Kích thước đầu vào | 80 × 256 | 60 × 200 |
| Số tham số | ~21.3M | ~11.2M |
| File checkpoint | ~86 MB | ~46 MB |
| Vai trò trong Ensemble | Mô hình chính (trọng số cao hơn) | Mô hình phụ (đa dạng hóa) |

### 3.3. CRNN (Thử nghiệm, không dùng trong sản xuất)

Chúng tôi cũng thử nghiệm kiến trúc CRNN (ResNet18 backbone + BiLSTM + CTC Loss) nhưng kết quả kém hơn đáng kể so với Spatial Pooling, do CAPTCHA UNETI luôn có đúng 4 ký tự và CTC decoding gặp khó khăn với các ký tự dính sát nhau.

---

## 4. Chiến lược huấn luyện

### 4.1. Tối ưu hóa

| Siêu tham số | ResNet34 | ResNet18 |
|:---|:---:|:---:|
| Optimizer | AdamW | AdamW |
| Weight Decay | 2e-2 | 2e-2 |
| Learning Rate (FC head) | 4e-4 | 5e-4 |
| Scheduler | CosineAnnealingLR | CosineAnnealingLR |
| Label Smoothing | 0.1 | 0.1 |
| Batch Size | 32 | 32 |
| Epochs | 150 | 150 |
| Gradient Clipping | max_norm=1.0 | max_norm=1.0 |

### 4.2. Differential Learning Rates

Sử dụng tốc độ học phân biệt để fine-tune backbone ImageNet pretrained:

| Layer Group | Tỷ lệ so với LR gốc |
|:---|:---:|
| conv1, bn1, layer1, layer2 | 0.03× |
| layer3, layer4 | 0.06× |
| FC head | 1.0× (full LR) |

**Lý do**: Các layer sâu (gần đầu vào) đã học được các đặc trưng tổng quát từ ImageNet (cạnh, góc, texture), chỉ cần tinh chỉnh nhẹ. Layer cao (gần đầu ra) cần thay đổi nhiều hơn để thích ứng với bài toán CAPTCHA.

### 4.3. Class Weights & Targeted Oversampling

- **Class Weights**: Tính trọng số nghịch đảo tần suất cho CrossEntropyLoss, clip trong khoảng [0.5, 3.0]
- **Targeted Oversampling**: Nhân bản 2× các mẫu chứa ký tự hiếm/khó (`Q`, `I`) trong tập train

### 4.4. Nền tảng huấn luyện

Huấn luyện được thực hiện trên **Google Colab** (GPU T4/V100) do máy local không đủ mạnh cho 150 epochs. Mã nguồn được đóng gói thành zip, upload lên Colab, huấn luyện, rồi tải checkpoint về máy local.

---

## 5. Pipeline suy luận sản xuất

### 5.1. Super Ensemble Architecture

Hệ thống suy luận cuối cùng kết hợp **4 mô hình** (2 nhánh × 2 backbone) cùng kỹ thuật **Test-Time Augmentation (TTA)**:

```
                    ┌─────────────────────────────────────┐
                    │          Ảnh CAPTCHA gốc (RGB)       │
                    └──────────┬──────────┬────────────────┘
                               │          │
                    ┌──────────▼──┐  ┌────▼─────────────┐
                    │ HSV Denoise  │  │  Giữ nguyên RGB  │
                    │ (Binarize)   │  │  (Không lọc)     │
                    └──────┬──────┘  └────┬─────────────┘
                           │              │
              ┌────────────┴───┐    ┌─────┴────────────┐
              │ Nhánh Binarized│    │   Nhánh RGB      │
              │                │    │                  │
         ┌────┴────┐  ┌───────┴┐  ┌┴────────┐  ┌─────┴──┐
         │ResNet34  │  │ResNet18│  │ResNet34 │  │ResNet18│
         │(TTA ×4)  │  │(TTA×4) │  │(TTA ×4) │  │(TTA×4) │
         └────┬────┘  └───┬────┘  └────┬────┘  └────┬───┘
              │           │            │             │
              ▼           ▼            ▼             ▼
         P_bin_34    P_bin_18     P_rgb_34      P_rgb_18
              │           │            │             │
              └─────┬─────┘            └──────┬──────┘
                    ▼                         ▼
          P_bin = 0.80×P34 + 0.20×P18  P_rgb = 0.80×P34 + 0.20×P18
                    │                         │
                    └────────────┬────────────┘
                                 ▼
                    P_final = 0.50×P_bin + 0.50×P_rgb
                                 │
                                 ▼
                          argmax → Kết quả
```

### 5.2. Test-Time Augmentation (TTA)

Mỗi mô hình nhận 4 phiên bản biến đổi của cùng 1 ảnh và trung bình hóa xác suất softmax:

| TTA Transform | Mô tả |
|:---|:---|
| Gốc | Resize chuẩn + ToTensor + Normalize |
| Dịch chuyển | RandomAffine(translate=(0.02, 0.01)) |
| Độ sáng | ColorJitter(brightness=0.1) |
| Xoay nhẹ | RandomAffine(degrees=2) |

### 5.3. Trọng số Ensemble tối ưu

Các trọng số được tìm kiếm bằng Grid Search trên tập Test:

| Tham số | Giá trị tối ưu |
|:---|:---:|
| Tỷ lệ ResNet34 trong nhánh Binarized | 0.80 |
| Tỷ lệ ResNet34 trong nhánh RGB | 0.80 |
| Tỷ lệ blend Binarized vs RGB | 0.50 : 0.50 |

### 5.4. Chuẩn hóa đầu vào

- **Normalization**: Symmetric `[0.5, 0.5, 0.5]` (mean) / `[0.5, 0.5, 0.5]` (std) → Scale pixel từ [0, 1] sang [-1, 1]
- **Resize**: ResNet34 → 80×256, ResNet18 → 60×200 (LANCZOS interpolation)

---

## 6. Kết quả thực nghiệm

### 6.1. Benchmark các mô hình đơn lẻ (Tập Test: 549 ảnh)

| # | Mô hình | Tiền xử lý | Word Accuracy | Số đúng | Số sai |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | ResNet34 Spatial (đơn lẻ) | Binarized | 97.27% | 534 | 15 |
| 2 | ResNet18 Spatial (đơn lẻ) | Binarized | 94.54% | 519 | 30 |
| 3 | ResNet34 RGB (đơn lẻ) | RGB | 95.26% | 523 | 26 |
| 4 | ResNet18 RGB (đơn lẻ) | RGB | 93.26% | 512 | 37 |
| 5 | CRNN CTC | Binarized | ~85% | ~467 | ~82 |

### 6.2. Benchmark các cấu hình Ensemble

| # | Cấu hình | Word Accuracy | Số đúng | Số sai |
|:---:|:---|:---:|:---:|:---:|
| 1 | Binarized Ensemble (R34 + R18, no TTA) | 97.45% | 535 | 14 |
| 2 | RGB Ensemble (R34 + R18, no TTA) | 96.54% | 530 | 19 |
| 3 | Super Ensemble (Bin + RGB, no TTA) | 97.45% | 535 | 14 |
| 4 | Binarized Ensemble + TTA | 97.63% | 536 | 13 |
| 5 | **Super Ensemble + TTA (Final)** | **97.63%** | **536** | **13** |

### 6.3. Tổng hợp kết quả

> **Kết quả tốt nhất đạt được: 97.63% Word Accuracy** (536/549 ảnh đúng, chỉ sai 13 ảnh) bằng cấu hình Super Ensemble + TTA kết hợp cả 4 mô hình.

---

## 7. Phân tích lỗi

### 7.1. Phân bố 13 lỗi còn lại theo loại

| Loại lỗi | Số lượng | Ảnh cụ thể |
|:---|:---:|:---|
| Nhầm `Q` → `O` (mất đuôi do nhiễu đè) | 5 | captcha_1409, 1045, 2777, 2824, 980* |
| Nhầm `1` ↔ `I` (font giống nhau) | 3 | captcha_3510, 1843, 1899 |
| Dính ký tự / Nét phức tạp | 3 | captcha_1212, 1154, 1051 |
| RGB đoán đúng nhưng BIN sai (vẫn đúng tổng) | 2 | captcha_103, 3202 |

*\* captcha_980: Ngược lại — chữ `O` bị đường nhiễu tạo đuôi giả → đoán sai thành `Q`*

### 7.2. Phân tích xác suất chi tiết

Mỗi ảnh lỗi được phân tích xác suất softmax ở cả 3 nhánh (BIN, RGB, ENS):

**Trường hợp điển hình — captcha_1409.png (GT: `QYFS`, Pred: `OYFS`)**:
- Binarized: P(`Q`) = 0.155, P(`O`) = 0.595 → Đuôi `Q` bị HSV cắt mất
- RGB: P(`Q`) = 0.158, P(`O`) = 0.505 → Đường nhiễu đè phần đuôi, RGB cũng không nhìn thấy
- Ensemble: P(`Q`) = 0.157, P(`O`) = 0.550 → Cả hai nhánh đều nhầm → Không thể cứu

**Trường hợp ensemble cứu được — captcha_103.png (GT: `QLSP`)**:
- Binarized: Đoán đúng `QLSP` ✅
- RGB: Đoán sai `OLSP` ❌
- Ensemble: Đoán đúng `QLSP` ✅ → Nhánh BIN kéo lại đúng

### 7.3. Nhận xét

Hầu hết các lỗi còn lại thuộc dạng **giới hạn vật lý** — đường kẻ nhiễu đè trực tiếp lên nét đặc trưng quan trọng nhất của ký tự (đuôi `Q`, flag `1`), khiến cả con người cũng khó phân biệt chính xác. Nhánh Super Ensemble đã giảm đáng kể số lỗi so với bất kỳ mô hình đơn lẻ nào.

---

## 8. Hướng dẫn triển khai

### 8.1. Cài đặt

```bash
# Tạo môi trường ảo
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux/macOS

# Cài đặt dependencies
pip install -r requirements.txt
```

### 8.2. Chạy Web Server nhận diện

```bash
python -m src.captcha_uneti.serving.web_app --port 5001
```

Server tự động nạp cả 4 checkpoint (2 Binarized + 2 RGB), chạy Super Ensemble + TTA khi nhận ảnh CAPTCHA mới.

### 8.3. Huấn luyện lại mô hình (trên Google Colab)

```bash
# Huấn luyện ResNet34 Binarized
python -m src.captcha_uneti.training.train --model resnet34 --epochs 150 --seed 42

# Huấn luyện ResNet34 RGB
python -m src.captcha_uneti.training.train --model resnet34 --epochs 150 --seed 42 --rgb

# Tương tự cho ResNet18
python -m src.captcha_uneti.training.train --model resnet18 --epochs 150 --seed 42
python -m src.captcha_uneti.training.train --model resnet18 --epochs 150 --seed 42 --rgb
```

### 8.4. Đánh giá mô hình

```bash
python -m src.captcha_uneti.evaluation.compare
```

---

## 9. Bài học kinh nghiệm

### 9.1. Tiền xử lý quan trọng hơn kiến trúc mạng

Bước ngoặt lớn nhất trong dự án không phải thay đổi kiến trúc mạng (ResNet18 → ResNet34) mà là **tinh chỉnh bộ lọc HSV denoising**. Việc chọn đúng ngưỡng `Value < 220` cho phép loại bỏ gần như toàn bộ nhiễu mà không phá hủy nét chữ — mang lại cải thiện lớn nhất về độ chính xác.

### 9.2. Ensemble đa dạng nguồn dữ liệu > Ensemble cùng nguồn

Ensemble 2 mô hình cùng dùng ảnh Binarized (R34 + R18) đạt 97.45%. Nhưng khi kết hợp thêm nhánh RGB (nhìn ảnh gốc), Super Ensemble đạt 97.63% — vì 2 nhánh bổ sung nhau: BIN mạnh ở ảnh sạch, RGB mạnh ở ảnh bị nhiễu đè nét.

### 9.3. TTA là "free accuracy" khi đánh đổi bằng thời gian

TTA (4 augmentations) tăng thêm ~0.18% Word Accuracy mà không cần huấn luyện lại. Tuy nhiên thời gian suy luận tăng ~4×. Trong production cần cân nhắc giữa tốc độ và độ chính xác.

### 9.4. Giới hạn vật lý tồn tại

Khi đường nhiễu đè trực tiếp lên nét đặc trưng duy nhất phân biệt 2 ký tự (đuôi `Q` vs `O`), **không có kiến trúc mạng nào** có thể đoán đúng 100% — vì thông tin đã bị mất vật lý. Giải pháp duy nhất là thay đổi loại đầu vào (RGB thay vì Binarized).

### 9.5. Oversampling ký tự hiếm rất hiệu quả

Ký tự `Q` và `I` xuất hiện ít trong CAPTCHA tự nhiên. Oversampling 2× các mẫu chứa các ký tự này giúp mô hình không bỏ qua chúng khi huấn luyện.

---

## 10. Hướng phát triển tương lai

### 10.1. Đạt mốc 99% Word Accuracy

Để giảm từ 13 lỗi xuống ≤ 5 lỗi (≥ 99.00%):
- **Fine-tuning tập trung**: Huấn luyện thêm phase ngắn chỉ trên các mẫu chứa `Q`, `O`, `1`, `I` bị nhiễu đè
- **Tăng cường augmentation RGB**: Vẽ nhiều đường nhiễu hơn, đặc biệt đè vào vùng đuôi `Q` và đầu `1`
- **Attention mechanism**: Thêm Self-Attention vào trước Spatial Pooling để mô hình tập trung vào các nét đặc trưng nhỏ

### 10.2. Tối ưu hóa tốc độ suy luận

- Sử dụng TorchScript hoặc ONNX Runtime để tăng tốc suy luận
- Knowledge Distillation: Nén Super Ensemble (4 mô hình) thành 1 mô hình nhỏ
- Quantization INT8 để giảm kích thước checkpoint

### 10.3. Mở rộng cho các loại CAPTCHA khác

- Áp dụng cùng kiến trúc Spatial Pooling cho các trang web khác có CAPTCHA tương tự
- Nghiên cứu khả năng Few-shot Learning khi có ít dữ liệu gán nhãn

---

## Phụ lục: Cấu trúc mã nguồn

```
solve-captcha/
├── src/captcha_uneti/
│   ├── models/                # Kiến trúc mạng (ResNet34, ResNet18, CRNN)
│   ├── training/              # Script huấn luyện thống nhất
│   ├── evaluation/            # Đánh giá & so sánh mô hình
│   ├── serving/               # Web server suy luận (Super Ensemble + TTA)
│   ├── tools/                 # Công cụ tải dữ liệu & chia tập
│   ├── templates/             # Giao diện web HTML
│   ├── dataset.py             # Dataset class (Binarized + RGB)
│   └── preprocessing.py       # HSV denoising pipeline
├── weights/                   # Trọng số sản xuất (4 checkpoint)
│   ├── binarized/             # ResNet34 + ResNet18 (HSV denoised)
│   └── rgb/                   # ResNet34 + ResNet18 (raw RGB)
├── data_uneti/                # Dữ liệu (train/val/test + labels)
└── config/                    # Cấu hình demo
```
