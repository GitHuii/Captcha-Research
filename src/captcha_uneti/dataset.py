"""
Dataset thống nhất cho CAPTCHA UNETI.
Hỗ trợ cấu hình kích thước ảnh, kiểu chuẩn hóa, và chế độ CTC.
"""
import os
import csv
import torch
import torchvision.transforms as T
from torch.utils.data import Dataset
from PIL import Image
import cv2
import numpy as np
import random

from .preprocessing import thresholded_denoise_random


class CaptchaDataset(Dataset):
    """
    Dataset thống nhất cho tất cả mô hình CAPTCHA UNETI.

    Args:
        csv_path: Đường dẫn tới file CSV chứa nhãn (image_name, label).
        img_dir: Thư mục chứa ảnh.
        alphabet: Danh sách ký tự (list of str).
        size: Kích thước ảnh đầu ra (height, width). Mặc định (80, 256).
        norm_type: Kiểu chuẩn hóa - "symmetric" ([0.5]*3) hoặc "imagenet".
        train: True = bật augmentation + random threshold, False = inference mode.
        for_ctc: True = trả nhãn dạng phẳng cho CTC Loss.
    """

    def __init__(self, csv_path, img_dir, alphabet, size=(80, 256),
                 norm_type="symmetric", train=True, for_ctc=False, rgb=False):
        self.img_dir = img_dir
        self.alphabet = alphabet
        self.char_to_idx = {c: i for i, c in enumerate(alphabet)}
        self.idx_to_char = {i: c for i, c in enumerate(alphabet)}
        self.train = train
        self.for_ctc = for_ctc
        self.rgb = rgb

        # Đọc dữ liệu từ CSV
        self.samples = []
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # bỏ header
            for row in reader:
                if len(row) == 2:
                    self.samples.append((row[0], row[1].strip().upper()))

        # Cấu hình chuẩn hóa
        if norm_type == "symmetric":
            norm = T.Normalize([0.5] * 3, [0.5] * 3)
        else:  # imagenet
            norm = T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

        # Cấu hình transforms
        if train:
            self.transform = T.Compose([
                T.Resize(size, interpolation=Image.Resampling.LANCZOS),
                T.RandomRotation(12),
                T.RandomAffine(degrees=8, translate=(0.06, 0.06), scale=(0.95, 1.05)),
                T.RandomPerspective(distortion_scale=0.15, p=0.5),
                T.ColorJitter(brightness=0.15, contrast=0.15),
                T.ToTensor(),
                norm,
            ])
        else:
            self.transform = T.Compose([
                T.Resize(size, interpolation=Image.Resampling.LANCZOS),
                T.ToTensor(),
                norm,
            ])

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_name, label = self.samples[idx]
        img = Image.open(os.path.join(self.img_dir, img_name)).convert('RGB')
        if not self.rgb:
            img = thresholded_denoise_random(img, is_train=self.train)
        else:
            if self.train:
                # Apply Synthetic Line Augmentation
                open_cv_image = np.array(img)
                open_cv_image = open_cv_image[:, :, ::-1].copy()
                h, w, _ = open_cv_image.shape
                num_lines = random.randint(1, 3)
                for _ in range(num_lines):
                    # Blue/cyan color range similar to noise (BGR format)
                    color = [random.randint(180, 255), random.randint(50, 150), random.randint(0, 100)]
                    pt1 = (random.randint(0, w), random.randint(0, h))
                    pt2 = (random.randint(0, w), random.randint(0, h))
                    thickness = random.randint(1, 2)
                    cv2.line(open_cv_image, pt1, pt2, color, thickness)
                img = Image.fromarray(open_cv_image[:, :, ::-1])
        tensor = self.transform(img)
        targets = torch.tensor(
            [self.char_to_idx.get(c, 0) for c in label[:4]], dtype=torch.long
        )

        if self.for_ctc:
            return tensor, targets, label
        return tensor, targets
