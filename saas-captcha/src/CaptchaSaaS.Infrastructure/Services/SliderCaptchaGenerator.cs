using System;
using System.IO;
using CaptchaSaaS.Core.Interfaces;
using Microsoft.Extensions.Configuration;
using SkiaSharp;

namespace CaptchaSaaS.Infrastructure.Services
{
    public class SliderCaptchaGenerator : ISliderCaptchaGenerator
    {
        private readonly string _backgroundsDirectory;
        private readonly Random _random = new Random();

        public SliderCaptchaGenerator(IConfiguration configuration)
        {
            var configuredPath = configuration["StorageSettings:BackgroundsDirectory"];
            if (string.IsNullOrWhiteSpace(configuredPath))
            {
                _backgroundsDirectory = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "assets", "backgrounds");
            }
            else
            {
                _backgroundsDirectory = Path.IsPathRooted(configuredPath)
                    ? configuredPath
                    : Path.Combine(Directory.GetCurrentDirectory(), configuredPath);
            }
        }

        public (double XTarget, int YOffset, byte[] BgImageBytes, byte[] BlockImageBytes) Generate()
        {
            // 1. Kiểm tra và chọn ảnh nền ngẫu nhiên
            if (!Directory.Exists(_backgroundsDirectory))
            {
                Directory.CreateDirectory(_backgroundsDirectory);
            }

            var files = Directory.GetFiles(_backgroundsDirectory, "*.png");
            if (files.Length == 0)
            {
                throw new FileNotFoundException($"No background images found in {_backgroundsDirectory}. Please run background image generation.");
            }

            var randomBgPath = files[_random.Next(files.Length)];

            // Kích thước chuẩn cho ảnh captcha
            const int width = 300;
            const int height = 150;
            const int puzzleSize = 40;
            const int r = 8; // Bán kính mấu lồi lõm của mảnh ghép
            const int blockSize = puzzleSize + 2 * r; // 56px

            // 2. Load ảnh nền gốc và scale về 300x150
            using var originalBitmap = SKBitmap.Decode(randomBgPath);
            using var bgBitmap = new SKBitmap(width, height);
            using var bgCanvas = new SKCanvas(bgBitmap);
            
            // Vẽ scale ảnh nền
            bgCanvas.DrawBitmap(originalBitmap, new SKRect(0, 0, originalBitmap.Width, originalBitmap.Height), new SKRect(0, 0, width, height));

            // 3. Chọn vị trí ngẫu nhiên cho mảnh ghép
            // Tránh sát lề trái (x < 60) và lề phải (x > 220) để có không gian trượt
            int xTarget = _random.Next(60, width - blockSize - 10);
            int yTarget = _random.Next(20, height - blockSize - 10);

            // 4. Tạo mảnh ghép trượt (Block Image) kích thước 56x56
            using var blockBitmap = new SKBitmap(blockSize, blockSize, SKColorType.Rgba8888, SKAlphaType.Premul);
            using var blockCanvas = new SKCanvas(blockBitmap);
            blockCanvas.Clear(SKColors.Transparent);

            // Path của mảnh ghép cục bộ (bắt đầu từ góc (r, r) tức (8,8) trong block 56x56)
            using var localPuzzlePath = CreatePuzzlePath(r, r, puzzleSize, r);

            // Thiết lập clipping path trên canvas của block để chỉ lấy phần ảnh trùng với mảnh ghép
            blockCanvas.Save();
            blockCanvas.ClipPath(localPuzzlePath, antialias: true);

            // Vẽ ảnh nền dịch chuyển sang trái/lên trên một khoảng đúng bằng vị trí cắt mảnh ghép
            // Cộng thêm r=8 để căn chỉnh vị trí khớp với canvas của mảnh ghép
            float shiftX = -(xTarget - r);
            float shiftY = -(yTarget - r);
            blockCanvas.DrawBitmap(bgBitmap, shiftX, shiftY);
            blockCanvas.Restore();

            // Vẽ viền sáng (Stroke) xung quanh mảnh ghép để tăng tính nhận diện
            using (var borderPaint = new SKPaint())
            {
                borderPaint.Color = SKColors.White.WithAlpha(200);
                borderPaint.Style = SKPaintStyle.Stroke;
                borderPaint.StrokeWidth = 1.5f;
                borderPaint.IsAntialias = true;
                blockCanvas.DrawPath(localPuzzlePath, borderPaint);
            }

            // 5. Vẽ lỗ khuyết (Shadow Hole) đè lên ảnh nền tại vị trí cắt
            using var globalPuzzlePath = CreatePuzzlePath(xTarget, yTarget, puzzleSize, r);
            
            // Làm tối vùng khuyết
            using (var shadowPaint = new SKPaint())
            {
                shadowPaint.Color = new SKColor(0, 0, 0, 160); // Màu đen mờ
                shadowPaint.Style = SKPaintStyle.Fill;
                shadowPaint.IsAntialias = true;
                bgCanvas.DrawPath(globalPuzzlePath, shadowPaint);
            }

            // Vẽ viền tối cho lỗ khuyết
            using (var shadowBorderPaint = new SKPaint())
            {
                shadowBorderPaint.Color = new SKColor(0, 0, 0, 200);
                shadowBorderPaint.Style = SKPaintStyle.Stroke;
                shadowBorderPaint.StrokeWidth = 2.0f;
                shadowBorderPaint.IsAntialias = true;
                bgCanvas.DrawPath(globalPuzzlePath, shadowBorderPaint);
            }

            // 6. Mã hóa cả hai ảnh thành mảng bytes PNG
            using var bgImage = SKImage.FromBitmap(bgBitmap);
            using var bgData = bgImage.Encode(SKEncodedImageFormat.Png, 90);

            using var blockImage = SKImage.FromBitmap(blockBitmap);
            using var blockData = blockImage.Encode(SKEncodedImageFormat.Png, 90);

            // Tọa độ X thực tế mà client cần trượt tới để khớp
            // Khi block đặt ở left=0 ban đầu, vị trí mảnh ghép là x=8 (r)
            // Lỗ khuyết trên nền ở vị trí xTarget.
            // Vậy khoảng cách cần trượt là: xTarget - r.
            double finalXTarget = xTarget - r;
            int finalYOffset = yTarget - r;

            return (finalXTarget, finalYOffset, bgData.ToArray(), blockData.ToArray());
        }

        private SKPath CreatePuzzlePath(float x, float y, float size, float r)
        {
            var path = new SKPath();
            
            path.MoveTo(x, y);

            // Cạnh trên: lồi ra ngoài (bulge out)
            path.LineTo(x + (size - r * 2) / 2f, y);
            path.CubicTo(
                x + (size - r * 2) / 2f, y - r,
                x + (size + r * 2) / 2f, y - r,
                x + (size + r * 2) / 2f, y
            );
            path.LineTo(x + size, y);

            // Cạnh phải: lõm vào trong (bulge in)
            path.LineTo(x + size, y + (size - r * 2) / 2f);
            path.CubicTo(
                x + size - r, y + (size - r * 2) / 2f,
                x + size - r, y + (size + r * 2) / 2f,
                x + size, y + (size + r * 2) / 2f
            );
            path.LineTo(x + size, y + size);

            // Cạnh dưới: lồi ra ngoài (bulge out)
            path.LineTo(x + (size + r * 2) / 2f, y + size);
            path.CubicTo(
                x + (size + r * 2) / 2f, y + size + r,
                x + (size - r * 2) / 2f, y + size + r,
                x + (size - r * 2) / 2f, y + size
            );
            path.LineTo(x, y + size);

            // Cạnh trái: lõm vào trong (bulge in)
            path.LineTo(x, y + (size + r * 2) / 2f);
            path.CubicTo(
                x + r, y + (size + r * 2) / 2f,
                x + r, y + (size - r * 2) / 2f,
                x, y + (size - r * 2) / 2f
            );
            path.LineTo(x, y);

            path.Close();
            return path;
        }
    }
}
