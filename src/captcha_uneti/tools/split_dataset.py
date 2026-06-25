"""
Phân tách dữ liệu CAPTCHA UNETI thành 3 phần: Train (70%), Val (15%), Test (15%).

Cách sử dụng:
    python -m src.captcha_uneti.tools.split_dataset
"""
import os
import shutil
import argparse
import pandas as pd


def split_dataset_3way(data_dir="data_uneti"):
    csv_path = os.path.join(data_dir, "labels.csv")
    images_src = os.path.join(data_dir, "images")

    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")
    test_dir = os.path.join(data_dir, "test")

    # Clean output dirs
    for d in [train_dir, val_dir, test_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"Total labeled images: {len(df)}")

    # Shuffle
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Split 70% Train, 15% Val, 15% Test
    total = len(df_shuffled)
    train_idx = int(total * 0.70)
    val_idx = int(total * 0.85)

    train_df = df_shuffled.iloc[:train_idx]
    val_df = df_shuffled.iloc[train_idx:val_idx]
    test_df = df_shuffled.iloc[val_idx:]

    print(f"Train samples (70%): {len(train_df)}")
    print(f"Val samples (15%): {len(val_df)}")
    print(f"Test samples (15%): {len(test_df)}")

    # Copy files
    for idx, row in train_df.iterrows():
        img_name = row.iloc[0]
        shutil.copy(os.path.join(images_src, img_name), os.path.join(train_dir, img_name))

    for idx, row in val_df.iterrows():
        img_name = row.iloc[0]
        shutil.copy(os.path.join(images_src, img_name), os.path.join(val_dir, img_name))

    for idx, row in test_df.iterrows():
        img_name = row.iloc[0]
        shutil.copy(os.path.join(images_src, img_name), os.path.join(test_dir, img_name))

    # Save CSVs
    train_df.to_csv(os.path.join(data_dir, "train_labels.csv"), index=False)
    val_df.to_csv(os.path.join(data_dir, "val_labels.csv"), index=False)
    test_df.to_csv(os.path.join(data_dir, "test_labels.csv"), index=False)

    print("Dataset successfully split into Train, Val, and Test sets!")


def main():
    parser = argparse.ArgumentParser(description="Chia tập dữ liệu CAPTCHA UNETI")
    parser.add_argument("--data_dir", type=str, default="data_uneti", help="Thư mục chứa dữ liệu")
    args = parser.parse_args()

    split_dataset_3way(args.data_dir)


if __name__ == "__main__":
    main()
