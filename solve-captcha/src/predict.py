import os
import json
import argparse
import torch
from PIL import Image
from dataset import get_transforms
from model import CaptchaModel

# File: solve-captcha/src/predict.py

def predict(image_path, model_path, alphabet_path):
    # Thiết lập thiết bị (CPU/GPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 1. Kiểm tra sự tồn tại của file model và bảng ký tự
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Không tìm thấy file model trọng số tại: {model_path}. Hãy chạy train.py trước!")
    if not os.path.exists(alphabet_path):
        raise FileNotFoundError(f"Không tìm thấy file bảng ký tự alphabet tại: {alphabet_path}.")

    # 2. Đọc bảng ký tự và xây dựng ánh xạ ngược (Index -> Chữ)
    with open(alphabet_path, 'r', encoding='utf-8') as f:
        alphabet = json.load(f)
    
    idx_to_char = {idx: char for idx, char in enumerate(alphabet)}
    num_classes = len(alphabet)

    # 3. Khởi tạo mô hình và nạp trọng số
    model = CaptchaModel(num_classes)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    # 4. Đọc và tiền xử lý ảnh đầu vào
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Không tìm thấy ảnh tại đường dẫn: {image_path}")
        
    image = Image.open(image_path).convert('RGB')
    
    # Áp dụng bộ biến đổi ảnh (transforms) và thêm chiều batch: (3, 60, 200) -> (1, 3, 60, 200)
    transform = get_transforms(train=False)
    image_tensor = transform(image).unsqueeze(0).to(device)

    # 5. Dự đoán
    with torch.no_grad():
        outputs = model(image_tensor) # Shape: (1, 4, num_classes)
        
        # Lấy chỉ số index có xác suất cao nhất tại mỗi vị trí trong 4 đầu phân loại
        _, preds = torch.max(outputs, dim=2) # Shape: (1, 4)
        
        # Giải mã chỉ số thành chuỗi văn bản ký tự
        predicted_chars = []
        for idx in preds[0].tolist():
            predicted_chars.append(idx_to_char.get(idx, '?'))
            
        predicted_text = "".join(predicted_chars)
        return predicted_text

def main():
    parser = argparse.ArgumentParser(description="Chạy dự đoán nhận diện một ảnh Captcha đơn lẻ bằng AI.")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn đến file ảnh Captcha cần giải (PNG/JPG)")
    parser.add_argument("--model_path", type=str, default="model/captcha_model.pth", help="Đường dẫn đến file model (.pth)")
    parser.add_argument("--alphabet_path", type=str, default="model/alphabet.json", help="Đường dẫn đến file alphabet.json")
    args = parser.parse_args()

    try:
        predicted_text = predict(args.image, args.model_path, args.alphabet_path)
        print(f"\n🔮 KẾT QUẢ DỰ ĐOÁN AI:")
        print(f"   Image File: {os.path.basename(args.image)}")
        print(f"   Predicted Text: {predicted_text}")
    except Exception as e:
        print(f"❌ Lỗi dự đoán: {e}")

if __name__ == "__main__":
    main()
