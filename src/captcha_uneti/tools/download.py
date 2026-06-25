"""
Tải ảnh CAPTCHA từ trang đăng nhập UNETI.

Cách sử dụng:
    python -m src.captcha_uneti.tools.download --count 500
"""
import os
import time
import csv
import string
import argparse

try:
    import ddddocr
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    print("Cần cài đặt: pip install ddddocr DrissionPage")
    exit(1)


def get_visible_captcha(page):
    """Tìm element captcha hiển thị trên trang."""
    try:
        captcha_imgs = page.eles('#newcaptcha')
        for img in captcha_imgs:
            rect = img.rect.size
            if rect and rect[0] > 0 and rect[1] > 0:
                return img
    except Exception:
        pass
    return None


def download_dataset(target_count=350, out_dir="data_uneti"):
    """Tải ảnh CAPTCHA mới từ UNETI login page."""
    ocr = ddddocr.DdddOcr(show_ad=False)

    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "labels.csv")

    existing_count = 0
    downloaded_records = []
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    for row in reader:
                        if len(row) == 2:
                            downloaded_records.append(row)
            existing_count = len(downloaded_records)
            print(f"Resuming download. Already have {existing_count} records.")
        except Exception as e:
            print(f"Error reading existing CSV: {e}. Starting fresh.")
            downloaded_records = []
            existing_count = 0

    csv_file = open(csv_path, 'a', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    if existing_count == 0:
        csv_writer.writerow(["image_name", "label"])
        csv_file.flush()

    page = None
    success_count = existing_count
    allowed_chars = set(string.ascii_letters + string.digits)

    try:
        while success_count < target_count:
            if page is None:
                print("Opening Chromium via DrissionPage...")
                co = ChromiumOptions()
                co.set_argument('--no-sandbox')
                co.set_argument('--disable-gpu')
                page = ChromiumPage(co)

                url_login = "https://sinhvien.uneti.edu.vn/sinh-vien-dang-nhap.html"
                print(f"Navigating to {url_login}...")
                try:
                    page.get(url_login)
                    print("Waiting 10 seconds for Cloudflare clearance...")
                    time.sleep(10)
                except Exception as e:
                    print(f"Navigation error: {e}. Retrying browser initialization...")
                    page.quit()
                    page = None
                    time.sleep(5)
                    continue

            visible_img = get_visible_captcha(page)
            if visible_img is None:
                print("Visible captcha element not found. Page might have reloaded or failed. Re-navigating...")
                try:
                    page.get("https://sinhvien.uneti.edu.vn/sinh-vien-dang-nhap.html")
                    time.sleep(5)
                except Exception:
                    print("Failed to re-navigate. Closing page to reopen...")
                    page.quit()
                    page = None
                time.sleep(2)
                continue

            try:
                loaded = False
                for _ in range(50):
                    if visible_img.run_js('return this.complete && this.naturalWidth > 0;'):
                        loaded = True
                        break
                    time.sleep(0.1)
            except Exception as e:
                print(f"Element state error (likely stale): {e}")
                time.sleep(1)
                continue

            if not loaded:
                print("Image failed to load in 5 seconds. Reloading captcha...")
                try:
                    page.run_js("""
                        var imgs = document.querySelectorAll('#newcaptcha');
                        var timestamp = new Date().getTime();
                        imgs.forEach(function(img) {
                            img.src = '/WebCommon/GetCaptcha?t=' + timestamp;
                        });
                    """)
                    time.sleep(1)
                except Exception:
                    pass
                continue

            temp_path = "temp_captcha_try.png"
            try:
                time.sleep(0.2)
                visible_img.get_screenshot(path=temp_path)
            except Exception as e:
                print(f"Screenshot error: {e}")
                time.sleep(1)
                continue

            try:
                with open(temp_path, "rb") as f:
                    img_bytes = f.read()
                label = ocr.classification(img_bytes)
                label = label.strip().upper()
            except Exception as e:
                print(f"OCR error: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                continue

            if os.path.exists(temp_path):
                os.remove(temp_path)

            is_valid = (len(label) == 4) and all(c in allowed_chars for c in label)

            if is_valid:
                img_name = f"captcha_{success_count}.png"
                dest_path = os.path.join(img_dir, img_name)

                try:
                    visible_img.get_screenshot(path=dest_path)
                    csv_writer.writerow([img_name, label])
                    csv_file.flush()
                    success_count += 1
                    print(f"[{success_count}/{target_count}] Labeled: {label} -> {img_name}")
                except Exception as e:
                    print(f"Failed to save final image: {e}")
            else:
                print(f"Discarding invalid OCR label: '{label}' (length={len(label)})")

            try:
                page.run_js("""
                    var imgs = document.querySelectorAll('#newcaptcha');
                    var timestamp = new Date().getTime();
                    imgs.forEach(function(img) {
                        img.src = '/WebCommon/GetCaptcha?t=' + timestamp;
                    });
                """)
                time.sleep(0.3)
            except Exception as e:
                print(f"Failed to trigger JS reload: {e}. Reopening browser...")
                page.quit()
                page = None
                time.sleep(3)

    except KeyboardInterrupt:
        print("Stopping downloader by user interrupt.")
    finally:
        csv_file.close()
        if page:
            page.quit()

    print(f"Finished. Total downloaded and auto-labeled: {success_count}")
    return success_count


def main():
    parser = argparse.ArgumentParser(description="Tải ảnh CAPTCHA từ UNETI")
    parser.add_argument("--count", type=int, default=500, help="Số lượng ảnh cần tải")
    parser.add_argument("--out", type=str, default="data_uneti", help="Thư mục lưu kết quả")
    args = parser.parse_args()

    download_dataset(target_count=args.count, out_dir=args.out)


if __name__ == "__main__":
    main()
