"""
Kiến trúc ResNet18 Spatial Pooling cho nhận diện CAPTCHA 4 ký tự.
Độ phân giải đầu vào: 60x200. Nhẹ hơn ResNet34, tốc độ suy luận nhanh gấp ~4.5 lần.
"""
import torch.nn as nn
import torchvision.models as models


class SpatialResNet18(nn.Module):
    """ResNet18 backbone với Spatial Pooling (2x4) cho 4 ký tự CAPTCHA."""

    def __init__(self, num_classes):
        super().__init__()
        r = models.resnet18(weights='IMAGENET1K_V1')
        self.conv1 = r.conv1
        self.bn1 = r.bn1
        self.relu = r.relu
        self.maxpool = r.maxpool
        self.layer1 = r.layer1
        self.layer2 = r.layer2
        self.layer3 = r.layer3
        self.layer4 = r.layer4
        self.pool = nn.AdaptiveAvgPool2d((2, 4))
        self.fc = nn.Sequential(
            nn.Linear(1024, 256), nn.ReLU(), nn.Dropout(0.5), nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.pool(x)
        x = x.permute(0, 3, 1, 2).reshape(x.size(0), 4, -1)
        return self.fc(x)
