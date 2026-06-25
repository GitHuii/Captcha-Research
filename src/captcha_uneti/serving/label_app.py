"""
Web app gán nhãn thủ công cho ảnh CAPTCHA UNETI.

Cách sử dụng:
    python -m src.captcha_uneti.serving.label_app --port 5002
"""
import os
import json
import base64
import glob
import csv
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import PyTorch & model dependencies cho gợi ý nhãn bằng AI
try:
    import torch
    import torchvision.transforms as T
    from PIL import Image
    from src.captcha_uneti.models import SpatialResNet34
    from src.captcha_uneti.preprocessing import thresholded_denoise
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class AIHelper:
    def __init__(self, model_path="weights/binarized/resnet34_seed42.pth", alphabet_path="weights/alphabet.json"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.enabled = False
        
        if not HAS_TORCH:
            print("PyTorch hoặc các thư viện phụ thuộc không khả dụng. Đã tắt gợi ý nhãn bằng AI.")
            return

        if not os.path.exists(model_path) or not os.path.exists(alphabet_path):
            print(f"Không tìm thấy file trọng số ({model_path}) hoặc file alphabet ({alphabet_path}). Đã tắt gợi ý nhãn bằng AI.")
            return

        try:
            with open(alphabet_path, encoding='utf-8') as f:
                self.alphabet = json.load(f)
            self.idx_to_char = {i: c for i, c in enumerate(self.alphabet)}
            
            self.model = SpatialResNet34(len(self.alphabet))
            self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=False))
            self.model.to(self.device).eval()
            
            self.transform = T.Compose([
                T.Resize((80, 256), interpolation=Image.Resampling.LANCZOS),
                T.ToTensor(),
                T.Normalize([0.5] * 3, [0.5] * 3),
            ])
            self.enabled = True
            print(f"Đã nạp mô hình AI {model_path} trên {self.device} để hỗ trợ tự động gợi ý nhãn!")
        except Exception as e:
            print(f"Lỗi khi nạp mô hình AI: {e}. Đã tắt gợi ý nhãn bằng AI.")

    def predict(self, img_path):
        if not self.enabled:
            return ""
        try:
            img = Image.open(img_path).convert('RGB')
            img = thresholded_denoise(img)
            tensor = self.transform(img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                out = self.model(tensor)
                preds = out.argmax(dim=2)
            result = "".join([self.idx_to_char[preds[0, i].item()] for i in range(4)]).upper()
            return result
        except Exception as e:
            print(f"Lỗi dự đoán AI cho {img_path}: {e}")
            return ""


class LabelingWebHandler(BaseHTTPRequestHandler):
    html_content = ""
    data_dir = "data_uneti"
    images_dir = "data_uneti/images"
    csv_path = "data_uneti/labels.csv"
    ai_helper = None
    conflicts_indices = []

    def log_message(self, format, *args):
        pass

    @classmethod
    def scan_conflicts(cls):
        print("Đang quét toàn bộ bộ dữ liệu để tìm các nhãn nghi ngờ sai lệch...")
        cls.conflicts_indices = []
        if not cls.ai_helper or not cls.ai_helper.enabled:
            print("Đã tắt quét sai lệch nhãn do AI helper chưa sẵn sàng.")
            return
        
        # Read labels from CSV
        labels_map = {}
        if os.path.exists(cls.csv_path):
            try:
                with open(cls.csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if len(row) == 2:
                            labels_map[row[0]] = row[1].strip().upper()
            except Exception as e:
                print(f"Lỗi đọc CSV quét sai lệch: {e}")
                return

        img_files = glob.glob(os.path.join(cls.images_dir, "captcha_*.png"))
        
        def get_index(fn_path):
            try:
                return int(os.path.basename(fn_path).split("_")[1].split(".")[0])
            except:
                return 99999
        img_files.sort(key=get_index)
        
        for fpath in img_files:
            filename = os.path.basename(fpath)
            csv_label = labels_map.get(filename, "")
            if csv_label:
                ai_label = cls.ai_helper.predict(fpath)
                if ai_label and ai_label != csv_label:
                    try:
                        idx = int(filename.split("_")[1].split(".")[0])
                        cls.conflicts_indices.append(idx)
                    except:
                        pass
        print(f"Quét hoàn tất! Tìm thấy {len(cls.conflicts_indices)} mẫu có nhãn mâu thuẫn với AI.")

    def get_labels_map(self):
        labels_map = {}
        if os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if len(row) == 2:
                            labels_map[row[0]] = row[1]
            except Exception as e:
                print(f"Error reading CSV: {e}")
        return labels_map

    def save_label(self, filename, label):
        labels_map = self.get_labels_map()
        if label:
            labels_map[filename] = label.strip().upper()
        else:
            if filename in labels_map:
                del labels_map[filename]

        try:
            def get_index(fn):
                try:
                    return int(fn.split("_")[1].split(".")[0])
                except:
                    return 99999

            sorted_keys = sorted(labels_map.keys(), key=get_index)

            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["image_name", "label"])
                for k in sorted_keys:
                    writer.writerow([k, labels_map[k]])
            return True
        except Exception as e:
            print(f"Error writing CSV: {e}")
            return False

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.html_content.encode('utf-8'))
            return

        if self.path == "/api/status":
            img_files = glob.glob(os.path.join(self.images_dir, "captcha_*.png"))
            total = len(img_files)
            labels = self.get_labels_map()
            labeled_count = len(labels)
            self.send_json_response({
                "total": total,
                "labeled": labeled_count,
                "labels": labels,
                "conflicts_count": len(LabelingWebHandler.conflicts_indices)
            })
            return

        if self.path == "/api/conflicts":
            self.send_json_response({"conflicts": LabelingWebHandler.conflicts_indices})
            return

        if self.path.startswith("/api/image"):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            try:
                index = int(query.get("index", [0])[0])
            except:
                index = 0

            filename = f"captcha_{index}.png"
            img_path = os.path.join(self.images_dir, filename)

            if not os.path.exists(img_path):
                self.send_json_response({"error": "Image not found"}, 404)
                return

            with open(img_path, "rb") as f:
                img_data = f.read()
            img_b64 = "data:image/png;base64," + base64.b64encode(img_data).decode('utf-8')

            labels = self.get_labels_map()
            current_label = labels.get(filename, "")
            labeled_count = len(labels)

            ai_suggest = ""
            if self.ai_helper:
                ai_suggest = self.ai_helper.predict(img_path)

            self.send_json_response({
                "index": index,
                "filename": filename,
                "image_base64": img_b64,
                "label": current_label,
                "ai_suggest": ai_suggest,
                "labeled_count": labeled_count
            })
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/save":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode('utf-8'))

                index = payload.get("index")
                label = payload.get("label", "").strip().upper()

                if index is None:
                    self.send_json_response({"error": "Index missing"}, 400)
                    return

                filename = f"captcha_{index}.png"
                success = self.save_label(filename, label)

                if success:
                    # Update conflicts list dynamically
                    if self.ai_helper and self.ai_helper.enabled:
                        img_path = os.path.join(self.images_dir, filename)
                        ai_label = self.ai_helper.predict(img_path)
                        if ai_label == label:
                            if index in LabelingWebHandler.conflicts_indices:
                                LabelingWebHandler.conflicts_indices.remove(index)
                        else:
                            if index not in LabelingWebHandler.conflicts_indices:
                                LabelingWebHandler.conflicts_indices.append(index)
                                LabelingWebHandler.conflicts_indices.sort()

                    print(f"Saved: {filename} -> '{label}'")
                    self.send_json_response({"success": True})
                else:
                    self.send_json_response({"error": "Save failed"}, 500)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        self.send_error(404, "Not Found")

    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description="CAPTCHA Manual Labeling Tool")
    parser.add_argument("--port", type=int, default=5002)
    args = parser.parse_args()

    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
    html_path = os.path.join(template_dir, "label_app.html")

    if not os.path.exists(html_path):
        print(f"HTML file not found: {html_path}")
        return

    with open(html_path, 'r', encoding='utf-8') as f:
        LabelingWebHandler.html_content = f.read()

    # Khởi tạo bộ gợi ý nhãn bằng AI sử dụng model ResNet18 mới nhất (94.86% Acc)
    model_path = "weights/binarized/resnet34_seed42.pth"
    alphabet_path = "weights/alphabet.json"
    try:
        LabelingWebHandler.ai_helper = AIHelper(model_path, alphabet_path)
        # Quét các mẫu mâu thuẫn nhãn giữa CSV và AI dự đoán
        LabelingWebHandler.scan_conflicts()
    except Exception as e:
        print(f"Không thể khởi tạo bộ gợi ý nhãn bằng AI: {e}")

    server_address = ('', args.port)
    httpd = HTTPServer(server_address, LabelingWebHandler)

    print("\n" + "=" * 60)
    print(f"CAPTCHA MANUAL LABELING TOOL IS ACTIVE!")
    print(f"Open in browser: http://localhost:{args.port}")
    print("=" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()
        print("Server stopped.")


if __name__ == "__main__":
    main()
