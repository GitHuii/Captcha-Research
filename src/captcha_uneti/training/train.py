"""
Script huấn luyện thống nhất cho tất cả mô hình CAPTCHA UNETI.

Cách sử dụng:
    python -m src.captcha_uneti.training.train --model resnet34 --epochs 150 --seed 42
    python -m src.captcha_uneti.training.train --model resnet18 --epochs 150 --seed 42
    python -m src.captcha_uneti.training.train --model crnn --epochs 250 --seed 42
"""
import os
import sys
import json
import argparse

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from src.captcha_uneti.models import SpatialResNet34, SpatialResNet18, CaptchaCRNN, decode_ctc, calculate_ctc_accuracy
from src.captcha_uneti.preprocessing import thresholded_denoise_random
from src.captcha_uneti.dataset import CaptchaDataset
from src.captcha_uneti.training.utils import set_seed, compute_class_weights

# Cấu hình mặc định cho từng mô hình
MODEL_CONFIGS = {
    "resnet34": {
        "class": SpatialResNet34,
        "size": (80, 256),
        "norm_type": "symmetric",
        "default_lr": 4e-4,
        "default_epochs": 150,
        "default_out": "weights/binarized/resnet34_seed{seed}.pth",
    },
    "resnet18": {
        "class": SpatialResNet18,
        "size": (60, 200),
        "norm_type": "symmetric",
        "default_lr": 5e-4,
        "default_epochs": 150,
        "default_out": "weights/binarized/resnet18_seed{seed}.pth",
    },
    "crnn": {
        "class": CaptchaCRNN,
        "size": (60, 200),
        "norm_type": "imagenet",
        "default_lr": 1e-3,
        "default_epochs": 250,
        "default_out": "weights/captcha_model_crnn.pth",
    },
}


def train_spatial(model_name, config, seed, out_path, epochs, lr, rgb):
    """Huấn luyện mô hình Spatial Pooling (ResNet18 hoặc ResNet34)."""
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training {model_name} seed={seed} on {device}, output={out_path}, rgb={rgb}")

    with open("weights/alphabet.json") as f:
        alphabet = json.load(f)
    num_classes = len(alphabet)

    train_ds = CaptchaDataset(
        "data_uneti/train_labels.csv", "data_uneti/train", alphabet,
        size=config["size"], norm_type=config["norm_type"], train=True, rgb=rgb
    )
    val_ds = CaptchaDataset(
        "data_uneti/val_labels.csv", "data_uneti/val", alphabet,
        size=config["size"], norm_type=config["norm_type"], train=False, rgb=rgb
    )

    # Targeted Oversampling of minority/confused classes (Q and I)
    if model_name.startswith("resnet"):
        target_chars = {'Q', 'I'}
        new_samples = []
        import random
        random.seed(seed)
        multiplier = 2.0
        orig_len = len(train_ds.samples)
        for img_name, label in train_ds.samples:
            has_target = any(c in target_chars for c in label)
            if has_target:
                floor_val = int(multiplier)
                frac_val = multiplier - floor_val
                copies = floor_val + (1 if random.random() < frac_val else 0)
                for _ in range(copies):
                    new_samples.append((img_name, label))
            else:
                new_samples.append((img_name, label))
        train_ds.samples = new_samples
        print(f"Targeted Oversampling (Q, I) enabled for {model_name}. Samples count: {len(train_ds.samples)} (originally {orig_len})")

    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=0, pin_memory=True)

    class_weights = compute_class_weights(train_ds.samples, train_ds.char_to_idx, num_classes).to(device)

    model = config["class"](num_classes).to(device)
    
    # Differential Learning Rates: fine-tune backbone slowly, head quickly
    optimizer = optim.AdamW([
        {'params': model.conv1.parameters(), 'lr': lr * 0.03},
        {'params': model.bn1.parameters(), 'lr': lr * 0.03},
        {'params': model.layer1.parameters(), 'lr': lr * 0.03},
        {'params': model.layer2.parameters(), 'lr': lr * 0.03},
        {'params': model.layer3.parameters(), 'lr': lr * 0.06},
        {'params': model.layer4.parameters(), 'lr': lr * 0.06},
        {'params': model.fc.parameters(), 'lr': lr}
    ], weight_decay=2e-2)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.1)

    best_val_word_acc = 0
    for epoch in range(1, epochs + 1):
        model.train()
        for imgs, targets in train_loader:
            imgs, targets = imgs.to(device), targets.to(device)
            optimizer.zero_grad()
            out = model(imgs)
            loss = sum(criterion(out[:, i], targets[:, i]) for i in range(4))
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        scheduler.step()

        if epoch % 5 == 0 or epoch == epochs:
            model.eval()
            correct_char = correct_word = total_char = total_word = 0
            with torch.no_grad():
                for imgs, targets in val_loader:
                    imgs, targets = imgs.to(device), targets.to(device)
                    out = model(imgs)
                    preds = out.argmax(dim=2)
                    for b in range(imgs.size(0)):
                        word_ok = True
                        for c in range(4):
                            total_char += 1
                            if preds[b, c] == targets[b, c]:
                                correct_char += 1
                            else:
                                word_ok = False
                        total_word += 1
                        if word_ok:
                            correct_word += 1

            char_acc = 100 * correct_char / total_char
            word_acc = 100 * correct_word / total_word
            print(f"Epoch [{epoch}/{epochs}] | Char Acc: {char_acc:.2f}% | Word Acc: {word_acc:.2f}%")
            if word_acc > best_val_word_acc:
                best_val_word_acc = word_acc
                torch.save(model.state_dict(), out_path)
                print(f"  -> Saved best (Word Acc: {word_acc:.2f}%)")

    print(f"\nBest Val Word Acc: {best_val_word_acc:.2f}%")
    return best_val_word_acc


def train_crnn(config, seed, out_path, epochs, lr, rgb):
    """Huấn luyện mô hình CRNN với CTC Loss."""
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training CRNN seed={seed} on {device}, output={out_path}, rgb={rgb}")

    with open("weights/alphabet.json") as f:
        alphabet = json.load(f)

    num_classes_ctc = len(alphabet) + 1  # +1 for CTC blank token
    idx_to_char_ctc = {0: "[blank]"}
    for i, c in enumerate(alphabet):
        idx_to_char_ctc[i + 1] = c

    train_ds = CaptchaDataset(
        "data_uneti/train_labels.csv", "data_uneti/train", alphabet,
        size=config["size"], norm_type=config["norm_type"], train=True, for_ctc=True, rgb=rgb
    )
    val_ds = CaptchaDataset(
        "data_uneti/val_labels.csv", "data_uneti/val", alphabet,
        size=config["size"], norm_type=config["norm_type"], train=False, for_ctc=True, rgb=rgb
    )

    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)

    model = CaptchaCRNN(num_classes_ctc).to(device)
    criterion = nn.CTCLoss(blank=0, zero_infinity=True)

    backbone_params = (
        list(model.conv1.parameters()) + list(model.bn1.parameters()) +
        list(model.layer1.parameters()) + list(model.layer2.parameters()) +
        list(model.layer3.parameters())
    )
    optimizer = optim.AdamW([
        {'params': backbone_params, 'lr': lr * 0.1},
        {'params': model.lstm.parameters(), 'lr': lr},
        {'params': model.fc.parameters(), 'lr': lr}
    ], weight_decay=1e-2)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    def get_actual_labels_list(labels_tensor):
        actuals = []
        for row in labels_tensor:
            chars = [train_ds.idx_to_char[idx] for idx in row.tolist()]
            actuals.append("".join(chars))
        return actuals

    best_word_acc = 0.0
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for images, labels, _ in train_loader:
            images, labels = images.to(device), labels.to(device)
            batch_size = images.size(0)
            optimizer.zero_grad()
            outputs = model(images)
            log_probs = outputs.log_softmax(2)
            input_lengths = torch.full((batch_size,), 16, dtype=torch.long, device=device)
            target_lengths = torch.full((batch_size,), 4, dtype=torch.long, device=device)
            targets = (labels + 1).view(-1)
            loss = criterion(log_probs, targets, input_lengths, target_lengths)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * batch_size

        # Evaluate on val set
        model.eval()
        val_char_correct = val_char_total = val_word_correct = val_word_total = 0
        with torch.no_grad():
            for images, labels, _ in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, dim=2)
                preds = preds.transpose(0, 1)
                decoded_preds = decode_ctc(preds, idx_to_char_ctc)
                actual_labels = get_actual_labels_list(labels)
                c_corr, c_tot, w_corr, w_tot = calculate_ctc_accuracy(decoded_preds, actual_labels)
                val_char_correct += c_corr
                val_char_total += c_tot
                val_word_correct += w_corr
                val_word_total += w_tot

        val_char_acc = 100 * val_char_correct / val_char_total
        val_word_acc = 100 * val_word_correct / val_word_total
        train_loss = running_loss / len(train_ds)
        scheduler.step()

        print(f"Epoch [{epoch}/{epochs}] | Loss: {train_loss:.4f} "
              f"| Val Char Acc: {val_char_acc:.2f}% | Val Word Acc: {val_word_acc:.2f}%")

        if val_word_acc >= best_word_acc or epoch == 1:
            best_word_acc = val_word_acc
            torch.save(model.state_dict(), out_path)
            print(f"  -> Saved best CRNN (Val Word Acc: {best_word_acc:.2f}%)")

    print(f"\nBest Val Word Acc: {best_word_acc:.2f}%")
    return best_word_acc


def main():
    parser = argparse.ArgumentParser(description="Huấn luyện mô hình CAPTCHA UNETI")
    parser.add_argument("--model", type=str, required=True, choices=["resnet34", "resnet18", "crnn"],
                        help="Kiểu mô hình: resnet34, resnet18, hoặc crnn")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=None, help="Số epoch (mặc định theo mô hình)")
    parser.add_argument("--lr", type=float, default=None, help="Learning rate (mặc định theo mô hình)")
    parser.add_argument("--out", type=str, default=None, help="Đường dẫn lưu model")
    parser.add_argument("--rgb", action="store_true", help="Huấn luyện trực tiếp trên ảnh RGB (không lọc HSV)")
    args = parser.parse_args()

    config = MODEL_CONFIGS[args.model]
    epochs = args.epochs or config["default_epochs"]
    lr = args.lr or config["default_lr"]
    out_path = args.out or config["default_out"].format(seed=args.seed)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if args.model == "crnn":
        train_crnn(config, args.seed, out_path, epochs, lr, args.rgb)
    else:
        train_spatial(args.model, config, args.seed, out_path, epochs, lr, args.rgb)


if __name__ == "__main__":
    main()
