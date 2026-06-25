"""
Kiến trúc CRNN (CNN + BiLSTM) với CTC Loss cho nhận diện CAPTCHA.
Độ phân giải đầu vào: 60x200.
"""
import torch
import torch.nn as nn
import torchvision.models as models


class CaptchaCRNN(nn.Module):
    """ResNet18 backbone + Bidirectional LSTM + CTC decoding."""

    def __init__(self, num_classes):
        super().__init__()
        resnet = models.resnet18(weights=None)
        self.conv1 = resnet.conv1
        self.bn1 = resnet.bn1
        self.relu = resnet.relu
        self.maxpool = resnet.maxpool
        self.layer1 = resnet.layer1
        self.layer2 = resnet.layer2
        self.layer3 = resnet.layer3
        self.pool = nn.AdaptiveAvgPool2d((1, 16))
        self.lstm = nn.LSTM(
            input_size=256, hidden_size=128, num_layers=2,
            bidirectional=True, dropout=0.3, batch_first=False
        )
        self.fc = nn.Linear(256, num_classes)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.pool(x)
        x = x.squeeze(2)
        x = x.permute(2, 0, 1)
        self.lstm.flatten_parameters()
        x, _ = self.lstm(x)
        return self.fc(x)


def decode_ctc(preds_tensor, idx_to_char):
    """Giải mã CTC: loại bỏ blank token (index 0) và ký tự lặp liên tiếp."""
    decoded_strings = []
    for row in preds_tensor:
        prev_val = None
        decoded = []
        for val in row.tolist():
            if val != 0:  # 0 is blank token
                if val != prev_val:
                    decoded.append(idx_to_char[val])
            prev_val = val
        decoded_strings.append("".join(decoded))
    return decoded_strings


def calculate_ctc_accuracy(decoded_preds, actual_labels):
    """Tính độ chính xác ký tự và từ cho kết quả CTC."""
    char_correct = 0
    total_chars = 0
    word_correct = 0
    total_words = len(actual_labels)

    for pred, actual in zip(decoded_preds, actual_labels):
        if pred == actual:
            word_correct += 1
        for p_char, a_char in zip(pred, actual):
            if p_char == a_char:
                char_correct += 1
        total_chars += len(actual)

    return char_correct, total_chars, word_correct, total_words
