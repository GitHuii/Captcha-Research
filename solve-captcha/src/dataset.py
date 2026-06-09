import os
import json
import pandas as pd
import torch
from torch.utils.data import Dataset
from PIL import Image
import torchvision.transforms as T

# Thư mục src/
# File: solve-captcha/src/dataset.py

class CaptchaDataset(Dataset):
    def __init__(self, csv_file, img_dir, transform=None, alphabet=None):
        self.df = pd.read_csv(csv_file)
        self.img_dir = img_dir
        self.transform = transform

        # Cấu hình bộ ký tự (Alphabet)
        if alphabet is None:
            # Tự động trích xuất các ký tự duy nhất xuất hiện trong file labels
            all_chars = set()
            for label in self.df['label'].dropna():
                all_chars.update(str(label))
            self.alphabet = sorted(list(all_chars))
        else:
            self.alphabet = alphabet

        self.char_to_idx = {char: idx for idx, char in enumerate(self.alphabet)}
        self.idx_to_char = {idx: char for idx, char in enumerate(self.alphabet)}

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        img_name = self.df.iloc[idx, 0]
        label_str = str(self.df.iloc[idx, 1])

        # Load ảnh dùng PIL
        img_path = os.path.join(self.img_dir, img_name)
        image = Image.open(img_path).convert('RGB') # Đọc dạng RGB (3 channels) để khớp với ResNet backbone

        if self.transform:
            image = self.transform(image)

        # Encode nhãn 4 ký tự thành mảng 4 số nguyên index
        label_tensor = torch.zeros(4, dtype=torch.long)
        for i, char in enumerate(label_str[:4]): # Giới hạn đúng 4 ký tự
            label_tensor[i] = self.char_to_idx.get(char, 0) # Fallback về index 0 nếu ký tự lạ

        return image, label_tensor

    def save_alphabet(self, file_path):
        """Lưu ánh xạ bảng ký tự để dùng cho việc Predict sau này"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.alphabet, f, ensure_ascii=False)

def get_transforms(train=True):
    """
    Trả về bộ biến đổi ảnh (transforms) cho dữ liệu.
    Dù dùng pre-trained hay không, ta sẽ chuyển ảnh sang Grayscale nhưng giữ 3 channels 
    để mô hình tập trung học hình dáng ký tự thay vì màu sắc.
    """
    transform_list = [
        T.Grayscale(num_output_channels=3), # Đổi sang Grayscale nhưng giữ 3 channels để khớp đầu vào ResNet
        T.Resize((60, 200)),               # Thay đổi kích thước về 200x60 (Height=60, Width=200)
        T.ToTensor(),                      # Chuyển thành Tensor và scale về [0, 1]
        T.Normalize(
            mean=[0.485, 0.456, 0.406],    # Chuẩn hóa theo chuẩn ImageNet
            std=[0.229, 0.224, 0.225]
        )
    ]
    return T.Compose(transform_list)
