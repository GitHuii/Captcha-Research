import os
import sys
import json
import base64
import io
from http.server import HTTPServer, BaseHTTPRequestHandler

# Thêm thư mục chứa file này vào python path để import các file cục bộ
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import torch
from PIL import Image
from dataset import get_transforms
from model import CaptchaModel

class CaptchaPredictor:
    def __init__(self, model_path, alphabet_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🖥️ Khởi tạo mô hình AI trên thiết bị: {self.device}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy file model trọng số tại: {model_path}.\nHãy đảm bảo bạn đã chép file mô hình tải từ Google Colab vào thư mục solve-captcha/model/")
        if not os.path.exists(alphabet_path):
            raise FileNotFoundError(f"Không tìm thấy bảng ký tự tại: {alphabet_path}.")

        # Đọc bảng ký tự
        with open(alphabet_path, 'r', encoding='utf-8') as f:
            self.alphabet = json.load(f)
            
        self.idx_to_char = {idx: char for idx, char in enumerate(self.alphabet)}
        
        # Tạo mô hình và nạp trọng số
        self.model = CaptchaModel(len(self.alphabet))
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        self.transform = get_transforms(train=False)
        print("🟢 Đã nạp thành công mô hình AI!")

    def predict_image(self, img_bytes):
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(image_tensor)
            _, preds = torch.max(outputs, dim=2)
            predicted_chars = [self.idx_to_char.get(idx, '?') for idx in preds[0].tolist()]
            return "".join(predicted_chars)

class CaptchaWebHandler(BaseHTTPRequestHandler):
    predictor = None
    html_content = ""

    def log_message(self, format, *args):
        # Tắt bớt log request mặc định để terminal sạch sẽ
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.html_content.encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/predict":
            try:
                # Đọc dữ liệu JSON từ request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode('utf-8'))
                
                image_b64 = payload.get("image", "")
                if "," in image_b64:
                    image_b64 = image_b64.split(",")[1]
                    
                if not image_b64:
                    self.send_json_response({"error": "Không tìm thấy dữ liệu ảnh."}, 400)
                    return
                
                # Giải mã Base64 và dự đoán kết quả
                image_bytes = base64.b64decode(image_b64)
                prediction = self.predictor.predict_image(image_bytes)
                
                print(f"🔮 [DỰ ĐOÁN] AI nhận diện được Captcha: [ {prediction} ]")
                self.send_json_response({"prediction": prediction}, 200)
            except Exception as e:
                print(f"❌ [LỖI DỰ ĐOÁN] {e}")
                self.send_json_response({"error": str(e)}, 500)
        else:
            self.send_error(404, "Not Found")

    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, "model", "captcha_model.pth")
    alphabet_path = os.path.join(base_dir, "model", "alphabet.json")
    html_path = os.path.join(current_dir, "index.html")
    
    # Đọc giao diện HTML
    if not os.path.exists(html_path):
        print(f"❌ Không tìm thấy file giao diện HTML tại: {html_path}")
        return
        
    with open(html_path, 'r', encoding='utf-8') as f:
        CaptchaWebHandler.html_content = f.read()

    # Khởi tạo bộ dự đoán
    try:
        CaptchaWebHandler.predictor = CaptchaPredictor(model_path, alphabet_path)
    except Exception as e:
        print(f"❌ Lỗi khởi tạo mô hình: {e}")
        print("Mẹo: Bạn đã copy file 'captcha_model.pth' và 'alphabet.json' vào thư mục 'solve-captcha/model/' chưa?")
        return

    # Chạy server
    port = 5001
    server_address = ('', port)
    httpd = HTTPServer(server_address, CaptchaWebHandler)
    
    print("\n" + "="*60)
    print(f"🎨 WEB APP AI CAPTCHA SOLVER ĐÃ SẴN SÀNG!")
    print(f"👉 Địa chỉ truy cập: http://localhost:{port}")
    print("="*60 + "\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng server...")
        httpd.server_close()
        print("🟢 Đã dừng server thành công.")

if __name__ == "__main__":
    main()
