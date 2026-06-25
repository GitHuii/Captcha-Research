"""
Web server nhận diện CAPTCHA UNETI với TTA Ensemble.

Cách sử dụng:
    python -m src.captcha_uneti.serving.web_app --port 5001
"""
import os
import sys
import json
import base64
import io
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

import torch
import torchvision.transforms as T
from PIL import Image

from src.captcha_uneti.models import SpatialResNet34, SpatialResNet18
from src.captcha_uneti.preprocessing import thresholded_denoise


class CaptchaPredictor:
    def __init__(self, model_paths_bin, model_paths_rgb, alphabet_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Khoi tao mo hinh AI tren thiet bi: {self.device}")

        if not os.path.exists(alphabet_path):
            raise FileNotFoundError(f"Khong tim thay bang ky tu tai: {alphabet_path}.")

        with open(alphabet_path, 'r', encoding='utf-8') as f:
            self.alphabet = json.load(f)

        self.idx_to_char = {idx: char for idx, char in enumerate(self.alphabet)}

        # Load binarized models
        self.models_bin = []
        for path in model_paths_bin:
            if os.path.exists(path):
                print(f"Dang nap model Binarized: {os.path.basename(path)}")
                if "resnet18" in path:
                    model = SpatialResNet18(len(self.alphabet))
                else:
                    model = SpatialResNet34(len(self.alphabet))
                model.load_state_dict(torch.load(path, map_location=self.device, weights_only=False))
                model.to(self.device).eval()
                self.models_bin.append(model)
            else:
                print(f"Khong tim thay file model Binarized tai: {path}")

        # Load RGB models
        self.models_rgb = []
        for path in model_paths_rgb:
            if os.path.exists(path):
                print(f"Dang nap model RGB: {os.path.basename(path)}")
                if "resnet18" in path:
                    model = SpatialResNet18(len(self.alphabet))
                else:
                    model = SpatialResNet34(len(self.alphabet))
                model.load_state_dict(torch.load(path, map_location=self.device, weights_only=False))
                model.to(self.device).eval()
                self.models_rgb.append(model)
            else:
                print(f"Khong tim thay file model RGB tai: {path}")

        self.norm = T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        
        # TTA transforms for ResNet34 (80x256)
        self.tta_34 = [
            T.Compose([T.Resize((80, 256), interpolation=Image.Resampling.LANCZOS), T.ToTensor(), self.norm]),
            T.Compose([T.Resize((80, 256), interpolation=Image.Resampling.LANCZOS),
                       T.RandomAffine(degrees=0, translate=(0.02, 0.01)), T.ToTensor(), self.norm]),
            T.Compose([T.Resize((80, 256), interpolation=Image.Resampling.LANCZOS),
                       T.ColorJitter(brightness=0.1), T.ToTensor(), self.norm]),
            T.Compose([T.Resize((80, 256), interpolation=Image.Resampling.LANCZOS),
                       T.RandomAffine(degrees=2), T.ToTensor(), self.norm]),
        ]

        # TTA transforms for ResNet18 (60x200)
        self.tta_18 = [
            T.Compose([T.Resize((60, 200), interpolation=Image.Resampling.LANCZOS), T.ToTensor(), self.norm]),
            T.Compose([T.Resize((60, 200), interpolation=Image.Resampling.LANCZOS),
                       T.RandomAffine(degrees=0, translate=(0.02, 0.01)), T.ToTensor(), self.norm]),
            T.Compose([T.Resize((60, 200), interpolation=Image.Resampling.LANCZOS),
                       T.ColorJitter(brightness=0.1), T.ToTensor(), self.norm]),
            T.Compose([T.Resize((60, 200), interpolation=Image.Resampling.LANCZOS),
                       T.RandomAffine(degrees=2), T.ToTensor(), self.norm]),
        ]
        print(f"Da nap thanh cong {len(self.models_bin)} Binarized va {len(self.models_rgb)} RGB models!")

    def predict_image(self, pil_img, denoised_img, n_tta=4):
        # We will collect prediction probabilities for Binarized branch
        probs_bin_list = []
        for model in self.models_bin:
            is_r18 = isinstance(model, SpatialResNet18)
            transforms = self.tta_18[:n_tta] if is_r18 else self.tta_34[:n_tta]
            
            probs_list = []
            for tfm in transforms:
                try:
                    tensor = tfm(denoised_img).unsqueeze(0).to(self.device)
                    with torch.no_grad():
                        logits = model(tensor)
                        probs = torch.softmax(logits, dim=2)[0]
                        probs_list.append(probs.cpu())
                except Exception as e:
                    print(f"Loi trong transform TTA (bin): {e}")
            if probs_list:
                probs_bin_list.append((is_r18, torch.stack(probs_list).mean(0)))

        # We will collect prediction probabilities for RGB branch
        probs_rgb_list = []
        for model in self.models_rgb:
            is_r18 = isinstance(model, SpatialResNet18)
            transforms = self.tta_18[:n_tta] if is_r18 else self.tta_34[:n_tta]
            
            probs_list = []
            for tfm in transforms:
                try:
                    tensor = tfm(pil_img).unsqueeze(0).to(self.device)
                    with torch.no_grad():
                        logits = model(tensor)
                        probs = torch.softmax(logits, dim=2)[0]
                        probs_list.append(probs.cpu())
                except Exception as e:
                    print(f"Loi trong transform TTA (rgb): {e}")
            if probs_list:
                probs_rgb_list.append((is_r18, torch.stack(probs_list).mean(0)))

        # Binarized branch ensemble (optimal weights: 0.80 ResNet34 + 0.20 ResNet18)
        if len(probs_bin_list) == 2:
            p34_b = probs_bin_list[0][1] if not probs_bin_list[0][0] else probs_bin_list[1][1]
            p18_b = probs_bin_list[1][1] if probs_bin_list[1][0] else probs_bin_list[0][1]
            p_bin = 0.80 * p34_b + 0.20 * p18_b
        elif probs_bin_list:
            p_bin = probs_bin_list[0][1]
        else:
            p_bin = None

        # RGB branch ensemble (optimal weights: 0.80 ResNet34 + 0.20 ResNet18)
        if len(probs_rgb_list) == 2:
            p34_r = probs_rgb_list[0][1] if not probs_rgb_list[0][0] else probs_rgb_list[1][1]
            p18_r = probs_rgb_list[1][1] if probs_rgb_list[1][0] else probs_rgb_list[0][1]
            p_rgb = 0.80 * p34_r + 0.20 * p18_r
        elif probs_rgb_list:
            p_rgb = probs_rgb_list[0][1]
        else:
            p_rgb = None

        # Final combination (optimal blend weight: 0.50 binarized + 0.50 RGB)
        if p_bin is not None and p_rgb is not None:
            p_ens = 0.50 * p_bin + 0.50 * p_rgb
        elif p_bin is not None:
            p_ens = p_bin
        elif p_rgb is not None:
            p_ens = p_rgb
        else:
            return "????"

        preds = p_ens.argmax(dim=1)
        return "".join([self.idx_to_char[p.item()] for p in preds]).upper()


class CaptchaWebHandler(BaseHTTPRequestHandler):
    predictor = None
    html_content = ""

    def log_message(self, format, *args):
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
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode('utf-8'))

                image_b64 = payload.get("image", "")
                if "," in image_b64:
                    image_b64 = image_b64.split(",")[1]

                if not image_b64:
                    self.send_json_response({"error": "Khong tim thay du lieu anh."}, 400)
                    return

                image_bytes = base64.b64decode(image_b64)
                pil_img = Image.open(io.BytesIO(image_bytes)).convert('RGB')

                denoised_img = thresholded_denoise(pil_img)

                buffered = io.BytesIO()
                denoised_img.save(buffered, format="PNG")
                denoised_b64 = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode('utf-8')

                prediction = self.predictor.predict_image(pil_img, denoised_img, n_tta=4)

                print(f"[DU DOAN] AI nhan dien duoc Captcha: [ {prediction} ]")
                self.send_json_response({
                    "prediction": prediction,
                    "denoised_image": denoised_b64
                }, 200)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[LOI DU DOAN] {e}")
                self.send_json_response({"error": str(e)}, 500)
        else:
            self.send_error(404, "Not Found")

    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description="Web App AI CAPTCHA Solver")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()

    model_paths_bin = [
        "weights/binarized/resnet34_seed42.pth",
        "weights/binarized/resnet18_seed42.pth"
    ]
    model_paths_rgb = [
        "weights/rgb/resnet34_seed42.pth",
        "weights/rgb/resnet18_seed42.pth"
    ]
    alphabet_path = "weights/alphabet.json"

    # Tìm file HTML template
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
    html_path = os.path.join(template_dir, "index.html")

    if not os.path.exists(html_path):
        print(f"HTML file not found: {html_path}")
        return

    with open(html_path, 'r', encoding='utf-8') as f:
        CaptchaWebHandler.html_content = f.read()

    try:
        CaptchaWebHandler.predictor = CaptchaPredictor(model_paths_bin, model_paths_rgb, alphabet_path)
    except Exception as e:
        print(f"Loi khoi tao mo hinh: {e}")
        return

    server_address = ('', args.port)
    httpd = HTTPServer(server_address, CaptchaWebHandler)

    print("\n" + "=" * 60)
    print(f"WEB APP AI CAPTCHA SOLVER DA SAN SANG!")
    print(f"Dia chi truy cap: http://localhost:{args.port}")
    print("=" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDang dung server...")
        httpd.server_close()
        print("Da dung server thanh cong.")


if __name__ == "__main__":
    main()
