import os
import shutil
import zipfile
import argparse
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Giải nén và phân tách Dataset Captcha thành tập Train và Test.")
    parser.add_argument("--zip", type=str, default="captcha_dataset.zip", 
                        help="Đường dẫn đến file ZIP xuất từ C# SaaS API (mặc định: captcha_dataset.zip)")
    parser.add_argument("--ratio", type=float, default=0.75, 
                        help="Tỷ lệ tập huấn luyện (mặc định: 0.75)")
    args = parser.parse_args()

    zip_path = args.zip
    
    # Nếu không tìm thấy file ở đường dẫn mặc định, tìm thử ở thư mục scratch
    if not os.path.exists(zip_path):
        scratch_zip = os.path.join("..", "..", "..", "..", "..", "captcha_dataset.zip") # Thư mục scratch của Agent
        if os.path.exists(scratch_zip):
            zip_path = scratch_zip
        else:
            # Tìm trong wwwroot của C# SaaS
            saas_zip = os.path.join("..", "saas-captcha", "src", "CaptchaSaaS.Api", "wwwroot", "captcha_dataset.zip")
            if os.path.exists(saas_zip):
                zip_path = saas_zip

    if not os.path.exists(zip_path):
        print(f"❌ Không tìm thấy file ZIP dataset tại: {args.zip}")
        print("Mẹo: Hãy gọi API xuất dataset từ C# SaaS trước hoặc copy file ZIP vào thư mục này.")
        return

    print(f"📦 Tìm thấy file ZIP tại: {zip_path}")
    print("🧹 Đang chuẩn bị các thư mục đầu ra...")
    
    # Xóa thư mục cũ nếu có để đảm bảo dữ liệu sạch
    data_dir = "data"
    train_dir = os.path.join(data_dir, "train")
    test_dir = os.path.join(data_dir, "test")
    
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
        
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    temp_extract_dir = "temp_dataset_extracted"
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)

    # 1. Giải nén file ZIP
    print("📂 Đang giải nén file ZIP...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    # 2. Đọc file CSV chứa nhãn
    csv_path = os.path.join(temp_extract_dir, "dataset.csv")
    if not os.path.exists(csv_path):
        print("❌ Lỗi: Không tìm thấy file dataset.csv bên trong file ZIP.")
        shutil.rmtree(temp_extract_dir)
        return

    df = pd.read_csv(csv_path)
    total_images = len(df)
    print(f"📊 Tổng số ảnh tìm thấy: {total_images}")

    if total_images < 4:
        print("❌ Lỗi: Số lượng ảnh quá ít để phân chia.")
        shutil.rmtree(temp_extract_dir)
        return

    # 3. Phân chia Dataset
    # Nếu số lượng ảnh lớn hơn hoặc bằng 4000, chúng ta sẽ cố gắng lấy đúng 3000 train và 1000 test
    if total_images >= 4000:
        print("🎯 Đang thực hiện phân chia cố định: 3.000 ảnh Train và 1.000 ảnh Test...")
        # Xáo trộn dữ liệu trước
        df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
        train_df = df_shuffled.iloc[:3000]
        test_df = df_shuffled.iloc[3000:4000]
    else:
        # Nếu ít hơn 4000, phân chia động theo tỷ lệ dùng Pandas
        print(f"⚠️ Số ảnh ({total_images}) ít hơn 4000. Phân chia theo tỷ lệ {args.ratio * 100}/{ (1 - args.ratio) * 100 }...")
        df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
        split_idx = int(len(df_shuffled) * args.ratio)
        if split_idx >= len(df_shuffled):
            split_idx = len(df_shuffled) - 1
        train_df = df_shuffled.iloc[:split_idx]
        test_df = df_shuffled.iloc[split_idx:]

    print(f"   + Số lượng tập Train: {len(train_df)}")
    print(f"   + Số lượng tập Test: {len(test_df)}")

    # 4. Sao chép ảnh vào các thư mục tương ứng
    print("💾 Đang phân phối các file ảnh...")
    
    def copy_images_and_build_df(subset_df, destination_dir):
        valid_rows = []
        for index, row in subset_df.iterrows():
            img_name = row['image_name']
            label = row['label']
            src_img_path = os.path.join(temp_extract_dir, "images", img_name)
            
            if os.path.exists(src_img_path):
                dest_img_path = os.path.join(destination_dir, img_name)
                shutil.copy(src_img_path, dest_img_path)
                valid_rows.append({'image_name': img_name, 'label': label})
            else:
                # Thử tìm ở thư mục gốc giải nén nếu không nằm trong thư mục images
                src_img_path_fallback = os.path.join(temp_extract_dir, img_name)
                if os.path.exists(src_img_path_fallback):
                    dest_img_path = os.path.join(destination_dir, img_name)
                    shutil.copy(src_img_path_fallback, dest_img_path)
                    valid_rows.append({'image_name': img_name, 'label': label})
        return pd.DataFrame(valid_rows)

    clean_train_df = copy_images_and_build_df(train_df, train_dir)
    clean_test_df = copy_images_and_build_df(test_df, test_dir)

    # Ghi file CSV nhãn mới
    clean_train_df.to_csv(os.path.join(data_dir, "train_labels.csv"), index=False)
    clean_test_df.to_csv(os.path.join(data_dir, "test_labels.csv"), index=False)

    # 5. Dọn dẹp thư mục tạm
    shutil.rmtree(temp_extract_dir)
    print("✨ Hoàn thành phân tách Dataset thành công!")
    print(f"📁 Dữ liệu được lưu tại thư mục: {os.path.abspath(data_dir)}")

if __name__ == "__main__":
    main()
