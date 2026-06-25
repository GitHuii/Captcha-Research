"""
CLI dự đoán đơn ảnh CAPTCHA UNETI.

Cách sử dụng:
    python -m src.captcha_uneti.serving.predict --image path/to/captcha.png
"""
import os
import json
import argparse

import torch
import torchvision.transforms as T
from PIL import Image

from src.captcha_uneti.models import SpatialResNet34
from src.captcha_uneti.preprocessing import thresholded_denoise


def predict(image_path, model_path="weights/binarized/resnet34_seed42.pth",
           alphabet_path="weights/alphabet.json"):
    """Dự đoán nhãn CAPTCHA từ một ảnh đơn."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with open(alphabet_path, encoding='utf-8') as f:
        alphabet = json.load(f)
    idx_to_char = {i: c for i, c in enumerate(alphabet)}

    model = SpatialResNet34(len(alphabet))
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=False))
    model.to(device).eval()

    transform = T.Compose([
        T.Resize((80, 256), interpolation=Image.Resampling.LANCZOS),
        T.ToTensor(),
        T.Normalize([0.5] * 3, [0.5] * 3),
    ])

    img = Image.open(image_path).convert('RGB')
    img = thresholded_denoise(img)
    tensor = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        out = model(tensor)
        preds = out.argmax(dim=2)

    result = "".join([idx_to_char[preds[0, i].item()] for i in range(4)]).upper()
    return result


def main():
    parser = argparse.ArgumentParser(description="Du doan CAPTCHA UNETI")
    parser.add_argument("--image", type=str, required=True, help="Duong dan toi anh captcha")
    parser.add_argument("--model", type=str, default="weights/binarized/resnet34_seed42.pth")
    parser.add_argument("--alphabet", type=str, default="weights/alphabet.json")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"Khong tim thay anh: {args.image}")
        return

    result = predict(args.image, args.model, args.alphabet)
    print(f"Ket qua: {result}")


if __name__ == "__main__":
    main()
