import os
import argparse
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from dataset import CaptchaDataset, get_transforms
from model import CaptchaModel

# File: solve-captcha/src/train.py

def calculate_accuracy(outputs, labels):
    """
    Tính toán độ chính xác ở cấp độ ký tự (character-level) 
    và cấp độ từ (word-level - đúng cả 4 ký tự).
    """
    # outputs shape: (batch_size, 4, num_classes)
    # labels shape: (batch_size, 4)
    _, preds = torch.max(outputs, dim=2) # preds shape: (batch_size, 4)
    
    # 1. Độ chính xác ký tự
    char_correct = (preds == labels).sum().item()
    total_chars = labels.numel()
    
    # 2. Độ chính xác từ (cả captcha)
    word_correct = (preds == labels).all(dim=1).sum().item()
    total_words = labels.size(0)
    
    return char_correct, total_chars, word_correct, total_words

def main():
    parser = argparse.ArgumentParser(description="Huấn luyện mô hình AI giải Captcha.")
    parser.add_argument("--epochs", type=int, default=15, help="Số epoch huấn luyện (mặc định: 15)")
    parser.add_argument("--batch_size", type=int, default=64, help="Kích thước batch (mặc định: 64)")
    parser.add_argument("--lr", type=float, default=0.001, help="Tốc độ học Learning Rate (mặc định: 0.001)")
    parser.add_argument("--data_dir", type=str, default="data", help="Thư mục chứa dữ liệu (mặc định: data)")
    parser.add_argument("--model_dir", type=str, default="model/v1", help="Thư mục lưu mô hình đầu ra (mặc định: model/v1)")
    args = parser.parse_args()

    # Thiết lập thiết bị chạy (Ưu tiên GPU CUDA)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️ Thiết bị sử dụng huấn luyện: {device}")

    # 1. Khởi tạo Dataset và Dataloader
    train_csv = os.path.join(args.data_dir, "train_labels.csv")
    train_img_dir = os.path.join(args.data_dir, "train")
    test_csv = os.path.join(args.data_dir, "test_labels.csv")
    test_img_dir = os.path.join(args.data_dir, "test")

    if not os.path.exists(train_csv) or not os.path.exists(test_csv):
        print("❌ Lỗi: Không tìm thấy file labels CSV. Vui lòng chạy split_dataset.py trước!")
        return

    print("📖 Đang nạp tập dữ liệu...")
    train_dataset = CaptchaDataset(train_csv, train_img_dir, transform=get_transforms(train=True))
    
    # Lưu bảng ký tự (alphabet) vào thư mục model để dùng khi Predict
    alphabet_file = os.path.join(args.model_dir, "alphabet.json")
    train_dataset.save_alphabet(alphabet_file)
    print(f"📝 Đã lưu bảng ký tự ({len(train_dataset.alphabet)} ký tự) tại: {alphabet_file}")

    # Tập test phải sử dụng chung bảng ký tự với tập train
    test_dataset = CaptchaDataset(test_csv, test_img_dir, transform=get_transforms(train=False), alphabet=train_dataset.alphabet)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=True)

    # 2. Khởi tạo Mô hình, Optimizer và Loss function
    num_classes = len(train_dataset.alphabet)
    model = CaptchaModel(num_classes).to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # Lưu lịch sử để vẽ đồ thị
    history = {
        'train_loss': [], 'test_loss': [],
        'train_word_acc': [], 'test_word_acc': []
    }

    best_word_acc = 0.0
    os.makedirs(args.model_dir, exist_ok=True)
    model_path = os.path.join(args.model_dir, "captcha_model.pth")

    print("\n🚀 Bắt đầu quá trình huấn luyện...")
    for epoch in range(args.epochs):
        # --- TRAIN EPOCH ---
        model.train()
        running_loss = 0.0
        train_char_correct, train_char_total = 0, 0
        train_word_correct, train_word_total = 0, 0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(images) # Shape: (batch_size, 4, num_classes)
            
            # Flatten outputs và labels để tính CrossEntropyLoss
            # outputs: (batch_size * 4, num_classes)
            # labels: (batch_size * 4)
            loss = criterion(outputs.view(-1, num_classes), labels.view(-1))
            
            # Backward pass & Optimize
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            
            # Tính độ chính xác
            c_corr, c_tot, w_corr, w_tot = calculate_accuracy(outputs, labels)
            train_char_correct += c_corr
            train_char_total += c_tot
            train_word_correct += w_corr
            train_word_total += w_tot

        epoch_train_loss = running_loss / len(train_dataset)
        epoch_train_char_acc = train_char_correct / train_char_total
        epoch_train_word_acc = train_word_correct / train_word_total

        # --- EVAL EPOCH ---
        model.eval()
        running_test_loss = 0.0
        test_char_correct, test_char_total = 0, 0
        test_word_correct, test_word_total = 0, 0

        with torch.no_grad():
            for images, labels in test_loader:
                images = images.to(device)
                labels = labels.to(device)

                outputs = model(images)
                loss = criterion(outputs.view(-1, num_classes), labels.view(-1))

                running_test_loss += loss.item() * images.size(0)
                
                c_corr, c_tot, w_corr, w_tot = calculate_accuracy(outputs, labels)
                test_char_correct += c_corr
                test_char_total += c_tot
                test_word_correct += w_corr
                test_word_total += w_tot

        epoch_test_loss = running_test_loss / len(test_dataset)
        epoch_test_char_acc = test_char_correct / test_char_total
        epoch_test_word_acc = test_word_correct / test_word_total

        # Ghi lịch sử
        history['train_loss'].append(epoch_train_loss)
        history['test_loss'].append(epoch_test_loss)
        history['train_word_acc'].append(epoch_train_word_acc)
        history['test_word_acc'].append(epoch_test_word_acc)

        print(f"Epoch [{epoch+1}/{args.epochs}] "
              f"| Loss: {epoch_train_loss:.4f} (Val: {epoch_test_loss:.4f}) "
              f"| Char Acc: {epoch_train_char_acc*100:.2f}% (Val: {epoch_test_char_acc*100:.2f}%) "
              f"| Word Acc: {epoch_train_word_acc*100:.2f}% (Val: {epoch_test_word_acc*100:.2f}%)")

        # Lưu mô hình tốt nhất (dựa trên độ chính xác cả từ - Word Accuracy)
        if epoch_test_word_acc >= best_word_acc or epoch == 0:
            best_word_acc = epoch_test_word_acc
            torch.save(model.state_dict(), model_path)
            print(f"⭐ Đã lưu mô hình tốt nhất với Val Word Acc: {best_word_acc*100:.2f}% tại {model_path}")

    print(f"\n🎉 Huấn luyện hoàn tất! Độ chính xác tập Test tốt nhất: {best_word_acc*100:.2f}%")

    # 3. Vẽ đồ thị Loss & Accuracy và lưu lại
    plt.figure(figsize=(12, 5))
    
    # Đồ thị Loss
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['test_loss'], label='Val Loss')
    plt.title('Training & Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    # Đồ thị Accuracy
    plt.subplot(1, 2, 2)
    plt.plot(history['train_word_acc'], label='Train Word Acc')
    plt.plot(history['test_word_acc'], label='Val Word Acc')
    plt.title('Captcha Word Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()

    plt.tight_layout()
    curves_path = os.path.join(args.model_dir, "training_curves.png")
    plt.savefig(curves_path)
    print(f"📊 Đồ thị huấn luyện được lưu tại: {curves_path}")

if __name__ == "__main__":
    main()
