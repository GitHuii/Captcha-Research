"""
Đánh giá và so sánh hiệu năng các mô hình CAPTCHA UNETI trên tập kiểm thử độc lập.

Cách sử dụng:
    python -m src.captcha_uneti.evaluation.compare
"""
import os
import json
import time

import torch
from torch.utils.data import DataLoader

from src.captcha_uneti.models import SpatialResNet34, SpatialResNet18, CaptchaCRNN, decode_ctc
from src.captcha_uneti.dataset import CaptchaDataset


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running evaluation comparison on: {device}\n")

    alphabet_path = "weights/alphabet.json"
    if not os.path.exists(alphabet_path):
        print(f"Error: {alphabet_path} not found.")
        return
    with open(alphabet_path, encoding='utf-8') as f:
        alphabet = json.load(f)

    num_classes = len(alphabet)
    idx_to_char = {i: c for i, c in enumerate(alphabet)}
    idx_to_char_ctc = {0: "[blank]"}
    for i, c in enumerate(alphabet):
        idx_to_char_ctc[i + 1] = c

    test_csv = "data_uneti/test_labels.csv"
    test_img_dir = "data_uneti/test"

    models_config = {
        "ResNet34 Spatial (80x256)": {
            "class": SpatialResNet34,
            "path": "weights/binarized/resnet34_seed42.pth",
            "size": (80, 256),
            "norm_type": "symmetric",
            "is_ctc": False,
            "num_classes": num_classes,
        },
        "ResNet18 Spatial (60x200)": {
            "class": SpatialResNet18,
            "path": "weights/binarized/resnet18_seed42.pth",
            "size": (60, 200),
            "norm_type": "symmetric",
            "is_ctc": False,
            "num_classes": num_classes,
        },
        "CRNN CTC (60x200)": {
            "class": CaptchaCRNN,
            "path": "weights/captcha_model_crnn.pth",
            "size": (60, 200),
            "norm_type": "imagenet",
            "is_ctc": True,
            "num_classes": num_classes + 1,
        },
    }

    results = []
    total_word = 0

    for name, config in models_config.items():
        print(f"Evaluating {name}...")
        model_path = config["path"]
        if not os.path.exists(model_path):
            print(f"  Warning: '{model_path}' not found. Skipping.")
            continue

        dataset = CaptchaDataset(
            test_csv, test_img_dir, alphabet,
            size=config["size"], norm_type=config["norm_type"],
            train=False, for_ctc=True
        )
        loader = DataLoader(dataset, batch_size=32, shuffle=False)

        model = config["class"](config["num_classes"]).to(device)
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=False))
        model.eval()

        correct_char = correct_word = total_char = 0
        total_word = 0

        start_time = time.time()
        with torch.no_grad():
            for imgs, targets, actual_labels in loader:
                imgs = imgs.to(device)
                if config["is_ctc"]:
                    outputs = model(imgs)
                    _, preds = torch.max(outputs, dim=2)
                    preds = preds.transpose(0, 1)
                    decoded_preds = decode_ctc(preds, idx_to_char_ctc)
                    for pred, actual in zip(decoded_preds, actual_labels):
                        pred = pred.upper()
                        if pred == actual:
                            correct_word += 1
                        for p_char, a_char in zip(pred, actual):
                            if p_char == a_char:
                                correct_char += 1
                        total_char += len(actual)
                        total_word += 1
                else:
                    outputs = model(imgs)
                    preds = outputs.argmax(dim=2)
                    for b in range(imgs.size(0)):
                        word_ok = True
                        for c in range(4):
                            total_char += 1
                            pred_char = idx_to_char[preds[b, c].item()]
                            if pred_char == actual_labels[b][c]:
                                correct_char += 1
                            else:
                                word_ok = False
                        total_word += 1
                        if word_ok:
                            correct_word += 1

        elapsed = time.time() - start_time
        char_acc = 100 * correct_char / total_char if total_char > 0 else 0
        word_acc = 100 * correct_word / total_word if total_word > 0 else 0
        avg_time_ms = (elapsed / total_word) * 1000 if total_word > 0 else 0

        results.append({
            "name": name,
            "char_acc": f"{char_acc:.2f}%",
            "word_acc": f"{word_acc:.2f}%",
            "avg_time": f"{avg_time_ms:.2f} ms",
            "correct_words": f"{correct_word}/{total_word}",
        })

    if not results:
        print("No models evaluated.")
        return

    # Print report
    print("\n" + "=" * 80)
    print("BÁO CÁO SO SÁNH KẾT QUẢ CÁC MÔ HÌNH TRÊN TẬP TEST")
    print("=" * 80)
    headers = ["Mô hình", "Word Acc", "Char Acc", "Thời gian", "Đúng"]
    print(f"| {headers[0]:<27} | {headers[1]:<10} | {headers[2]:<10} | {headers[3]:<12} | {headers[4]:<10} |")
    print(f"|{'-' * 29}|{'-' * 12}|{'-' * 12}|{'-' * 14}|{'-' * 12}|")
    for r in results:
        print(f"| {r['name']:<27} | {r['word_acc']:<10} | {r['char_acc']:<10} | {r['avg_time']:<12} | {r['correct_words']:<10} |")
    print("=" * 80)

    # Save markdown report
    report = "# Báo cáo So sánh Mô hình CAPTCHA UNETI\n\n"
    report += f"Đánh giá trên tập Test độc lập ({total_word} mẫu).\n\n"
    report += "| Mô hình | Word Acc | Char Acc | Thời gian / mẫu | Số đúng |\n"
    report += "| :--- | :---: | :---: | :---: | :---: |\n"
    for r in results:
        report += f"| {r['name']} | **{r['word_acc']}** | {r['char_acc']} | {r['avg_time']} | {r['correct_words']} |\n"

    report_path = "weights/model_comparison_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSaved report to {report_path}")


if __name__ == "__main__":
    main()
