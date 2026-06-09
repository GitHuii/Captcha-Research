using System;
using System.IO;
using System.Text;
using CaptchaSaaS.Core.Interfaces;
using Microsoft.Extensions.Configuration;
using SkiaSharp;

namespace CaptchaSaaS.Infrastructure.Services
{
    public class CaptchaGenerator : ICaptchaGenerator
    {
        private readonly string _characterPool;
        private readonly Random _random = new Random();

        // Danh sách màu sắc tông xanh dương/tím/chàm đậm giống hình mẫu
        private readonly SKColor[] _colors = new SKColor[]
        {
            SKColor.Parse("#1A237E"), // Indigo Dark
            SKColor.Parse("#0D47A1"), // Blue Dark
            SKColor.Parse("#311B92"), // Deep Purple Dark
            SKColor.Parse("#4A148C"), // Purple Dark
            SKColor.Parse("#004D40"), // Teal Dark
            SKColor.Parse("#1565C0"), // Cobalt Blue
            SKColor.Parse("#283593")  // Dark Blue-grey
        };

        public CaptchaGenerator(IConfiguration configuration)
        {
            // Cấu hình ký tự ngẫu nhiên trong appsettings.json, mặc định loại bỏ ký tự dễ nhầm lẫn
            _characterPool = configuration["CaptchaSettings:CharacterPool"] 
                ?? "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        }

        public (string Text, byte[] ImageBytes) Generate(int length = 4)
        {
            // 1. Sinh chuỗi ký tự ngẫu nhiên
            var captchaText = GenerateRandomText(length);

            // Kích thước ảnh captcha chuẩn
            const int width = 200;
            const int height = 60;

            // 2. Khởi tạo Bitmap và Canvas nền trắng
            using var bitmap = new SKBitmap(width, height);
            using var canvas = new SKCanvas(bitmap);
            canvas.Clear(SKColors.White);

            // 3. Vẽ chữ nhiễu và xoay (Text Drawing)
            DrawText(canvas, captchaText, width, height);

            // 4. Vẽ các đường kẻ gây nhiễu cắt qua chữ (Interference Lines)
            DrawNoiseLines(canvas, width, height);

            // 5. Vẽ hạt nhiễu tròn xung quanh (Salt & Pepper Noise)
            DrawNoisePoints(canvas, width, height);

            // 6. Mã hóa Bitmap thành mảng byte dạng PNG
            using var image = SKImage.FromBitmap(bitmap);
            using var data = image.Encode(SKEncodedImageFormat.Png, 100);
            
            return (captchaText, data.ToArray());
        }

        private string GenerateRandomText(int length)
        {
            var result = new StringBuilder(length);
            for (int i = 0; i < length; i++)
            {
                result.Append(_characterPool[_random.Next(_characterPool.Length)]);
            }
            return result.ToString();
        }

        private void DrawText(SKCanvas canvas, string text, int width, int height)
        {
            float startX = 20f;
            float stepX = (width - 40f) / text.Length;
            
            // Sử dụng font hệ thống mặc định đậm
            using var typeface = SKTypeface.FromFamilyName("Arial", SKFontStyle.Bold);

            for (int i = 0; i < text.Length; i++)
            {
                var charStr = text[i].ToString();
                var fontSize = _random.Next(32, 38);
                var color = _colors[_random.Next(_colors.Length)];

                using var font = new SKFont(typeface, fontSize)
                {
                    Embolden = true
                };

                using var paint = new SKPaint
                {
                    Color = color,
                    IsAntialias = true
                };

                // Tính toán vị trí X và Y ngẫu nhiên nhẹ cho từng ký tự
                float x = startX + (i * stepX) + _random.Next(-5, 5);
                float y = (height / 2f) + (fontSize / 3f) + _random.Next(-4, 4);

                // Xoay ký tự
                float angle = _random.Next(-15, 16); // Xoay từ -15 đến +15 độ

                canvas.Save();
                canvas.Translate(x, y);
                canvas.RotateDegrees(angle);
                
                // Vẽ ký tự tại điểm gốc mới (0,0) sau khi dịch chuyển và xoay
                canvas.DrawText(charStr, 0, 0, SKTextAlign.Left, font, paint);
                canvas.Restore();
            }
        }

        private void DrawNoiseLines(SKCanvas canvas, int width, int height)
        {
            int lineCount = _random.Next(2, 5); // Vẽ từ 2 đến 4 đường cong

            for (int i = 0; i < lineCount; i++)
            {
                var color = _colors[_random.Next(_colors.Length)];
                using var paint = new SKPaint
                {
                    Color = color,
                    Style = SKPaintStyle.Stroke,
                    StrokeWidth = (float)(_random.NextDouble() * 1.5 + 1.2), // Độ dày từ 1.2px đến 2.7px
                    IsAntialias = true
                };

                using var path = new SKPath();
                
                // Vẽ đường cong Bezier xuất phát từ cạnh trái sang cạnh phải
                float startY = _random.Next(10, height - 10);
                float endY = _random.Next(10, height - 10);
                
                path.MoveTo(0, startY);
                
                // Điểm điều khiển Bezier ngẫu nhiên
                float ctrlX1 = width / 3f + _random.Next(-20, 20);
                float ctrlY1 = _random.Next(0, height);
                float ctrlX2 = 2 * width / 3f + _random.Next(-20, 20);
                float ctrlY2 = _random.Next(0, height);

                path.CubicTo(ctrlX1, ctrlY1, ctrlX2, ctrlY2, width, endY);

                canvas.DrawPath(path, paint);
            }
        }

        private void DrawNoisePoints(SKCanvas canvas, int width, int height)
        {
            int pointCount = _random.Next(120, 180); // Rải 120-180 chấm nhiễu

            for (int i = 0; i < pointCount; i++)
            {
                var color = _colors[_random.Next(_colors.Length)];
                using var paint = new SKPaint
                {
                    Color = color,
                    Style = SKPaintStyle.Fill,
                    IsAntialias = true
                };

                float x = _random.Next(0, width);
                float y = _random.Next(0, height);
                float radius = (float)(_random.NextDouble() * 0.8 + 0.6); // Bán kính hạt nhiễu từ 0.6px đến 1.4px

                canvas.DrawCircle(x, y, radius, paint);
            }
        }
    }
}
