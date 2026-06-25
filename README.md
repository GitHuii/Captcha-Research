# 🔓 CAPTCHA UNETI Solver — Deep Learning

Hệ thống nhận diện CAPTCHA tự động cho Đại học Kinh tế - Kỹ thuật Công nghiệp (UNETI), sử dụng kiến trúc **Super Ensemble** kết hợp 4 mô hình CNN (ResNet34 + ResNet18, Binarized + RGB) cùng **Test-Time Augmentation (TTA)**.

> **Kết quả tốt nhất**: **97.63% Word Accuracy** (536/549 ảnh test đúng)

---

## 📁 Cấu trúc dự án

```
Captcha-Research/ (Project Root)
├── README.md                  # Hướng dẫn sử dụng
├── REPORT.md                  # Báo cáo nghiên cứu tổng kết chi tiết
├── requirements.txt           # Thư viện Python cần thiết
│
├── src/captcha_uneti/         # Package chính
│   ├── models/                # Kiến trúc mạng (ResNet34, ResNet18, CRNN)
│   ├── training/              # Script huấn luyện thống nhất
│   ├── evaluation/            # Đánh giá & so sánh mô hình
│   ├── serving/               # Web server suy luận + gán nhãn
│   ├── tools/                 # Tải dữ liệu & chia tập
│   ├── templates/             # Giao diện HTML
│   ├── dataset.py             # Dataset class
│   └── preprocessing.py       # HSV denoising pipeline
│
├── weights/                   # Trọng số sản xuất
│   ├── alphabet.json          # Bộ ký tự 36 lớp (0-9, A-Z)
│   ├── binarized/             # Nhánh Binarized (HSV denoised)
│   │   ├── resnet34_seed42.pth
│   │   └── resnet18_seed42.pth
│   └── rgb/                   # Nhánh RGB (raw image)
│       ├── resnet34_seed42.pth
│       └── resnet18_seed42.pth
│
├── data_uneti/                # Dữ liệu (train/val/test)
│   ├── train/                 # 2559 ảnh huấn luyện
│   ├── val/                   # 548 ảnh validation
│   ├── test/                  # 549 ảnh kiểm thử
│   └── *.csv                  # File nhãn
│
└── config/                    # Cấu hình
    └── demo_keys.json
```

---

## ⚙️ Cài đặt

```bash
# Tạo môi trường ảo
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS

# Cài đặt dependencies
pip install -r requirements.txt
```

---

## 🚀 Sử dụng

### Chạy Web Server nhận diện CAPTCHA

```bash
python -m src.captcha_uneti.serving.web_app --port 5001
```

Truy cập [http://localhost:5001](http://localhost:5001) — Kéo thả hoặc upload ảnh CAPTCHA để nhận kết quả.

### Dự đoán ảnh đơn lẻ (CLI)

```bash
python -m src.captcha_uneti.serving.predict --image path/to/captcha.png
```

### Đánh giá mô hình trên tập test

```bash
python -m src.captcha_uneti.evaluation.compare
```

### Huấn luyện mô hình (Google Colab / GPU)

```bash
# === HUẤN LUYỆN RESNET34 ===
# ResNet34 Binarized (HSV Denoised)
python -m src.captcha_uneti.training.train --model resnet34 --epochs 150 --seed 42

# ResNet34 RGB (Raw Image)
python -m src.captcha_uneti.training.train --model resnet34 --epochs 150 --seed 42 --rgb

# === HUẤN LUYỆN RESNET18 ===
# ResNet18 Binarized (HSV Denoised)
python -m src.captcha_uneti.training.train --model resnet18 --epochs 150 --seed 42

# ResNet18 RGB (Raw Image)
python -m src.captcha_uneti.training.train --model resnet18 --epochs 150 --seed 42 --rgb
```

### Gán nhãn thủ công (Label Tool)

```bash
python -m src.captcha_uneti.serving.label_app --port 5002
```

---

## 📊 Kết quả

| Cấu hình | Word Accuracy | Số đúng / Tổng |
|:---|:---:|:---:|
| ResNet34 đơn lẻ (Binarized) | 97.27% | 534 / 549 |
| Ensemble Binarized (R34 + R18) | 97.45% | 535 / 549 |
| **Super Ensemble + TTA** | **97.63%** | **536 / 549** |

> Xem [REPORT.md](REPORT.md) để biết chi tiết đầy đủ về phương pháp, kiến trúc, và phân tích lỗi.
