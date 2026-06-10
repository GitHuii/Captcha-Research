import torch
import torch.nn as nn
import torchvision.models as models

# File: solve-captcha/src/model.py

class CaptchaModel(nn.Module):
    def __init__(self, num_classes):
        super(CaptchaModel, self).__init__()
        
        # Load backbone ResNet18 với cơ chế fallback tương thích nhiều phiên bản torchvision
        try:
            # Phiên bản torchvision mới
            self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
            print("INFO: Loaded ResNet18 with default pre-trained weights.")
        except (AttributeError, ValueError):
            try:
                # Phiên bản cũ hơn
                self.backbone = models.resnet18(pretrained=True)
                print("INFO: Loaded ResNet18 with pretrained=True fallback.")
            except Exception:
                # Chạy không tải weights pre-trained (nếu offline)
                self.backbone = models.resnet18(weights=None)
                print("WARNING: Loaded ResNet18 without pre-trained weights.")

        # Lấy kích thước đầu vào của lớp Fully Connected (fc) gốc
        num_features = self.backbone.fc.in_features
        
        # Loại bỏ lớp fc gốc bằng cách gán nó thành Identity
        self.backbone.fc = nn.Identity()

        # Định nghĩa 4 đầu phân loại song song cho 4 vị trí ký tự
        self.fc1 = nn.Linear(num_features, num_classes)
        self.fc2 = nn.Linear(num_features, num_classes)
        self.fc3 = nn.Linear(num_features, num_classes)
        self.fc4 = nn.Linear(num_features, num_classes)

    def forward(self, x):
        # Trích xuất đặc trưng qua ResNet18 backbone
        features = self.backbone(x) # Shape: (batch_size, 512)

        # Đưa qua 4 đầu phân loại
        out1 = self.fc1(features)   # Shape: (batch_size, num_classes)
        out2 = self.fc2(features)
        out3 = self.fc3(features)
        out4 = self.fc4(features)

        # Xếp chồng 4 đầu ra thành một tensor kết quả duy nhất
        # Shape đầu ra: (batch_size, 4, num_classes)
        return torch.stack([out1, out2, out3, out4], dim=1)

if __name__ == "__main__":
    # Test cấu trúc mạng
    model = CaptchaModel(32)
    test_input = torch.randn(2, 3, 60, 200) # Batch size=2, 3 channels, 200x60
    output = model(test_input)
    print("Output shape:", output.shape) # Kỳ vọng: torch.Size([2, 4, 32])
