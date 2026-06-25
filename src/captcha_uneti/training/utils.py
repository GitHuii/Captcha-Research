"""
Các hàm tiện ích dùng chung cho quá trình huấn luyện.
"""
import random
import numpy as np
import torch


def set_seed(seed):
    """Đặt seed cho tất cả bộ sinh số ngẫu nhiên để đảm bảo kết quả tái lập."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def compute_class_weights(samples, char_to_idx, num_classes, clip_range=(0.5, 3.0)):
    """
    Tính class weights dựa trên tần suất xuất hiện của từng ký tự trong tập train.
    Ký tự hiếm sẽ có trọng số cao hơn để mô hình chú ý nhiều hơn.

    Args:
        samples: List of (filename, label) tuples.
        char_to_idx: Dict ánh xạ ký tự -> index.
        num_classes: Tổng số lớp (ký tự).
        clip_range: Giới hạn trọng số (min, max).

    Returns:
        torch.FloatTensor: Vector trọng số cho CrossEntropyLoss.
    """
    char_counts = np.zeros(num_classes)
    for _, label in samples:
        for char in label:
            if char in char_to_idx:
                char_counts[char_to_idx[char]] += 1
    char_counts = np.maximum(char_counts, 1.0)

    weights = len(samples) * 4.0 / (num_classes * char_counts)
    weights = weights / np.mean(weights)
    weights = np.clip(weights, clip_range[0], clip_range[1])
    return torch.FloatTensor(weights)
