using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using CaptchaSaaS.Core.Interfaces;

namespace CaptchaSaaS.Infrastructure.Services
{
    public class ImageGridGenerator : IImageGridGenerator
    {
        private readonly string[] _categories = { "car", "dog", "cat", "tree" };
        private readonly Dictionary<string, string> _prompts = new Dictionary<string, string>
        {
            { "car", "Xe hơi" },
            { "dog", "Chó" },
            { "cat", "Mèo" },
            { "tree", "Cây cối" }
        };

        public ImageGridGenerator()
        {
        }

        public ImageGridChallengeResult GenerateChallenge(string baseRequestUrl)
        {
            var rand = new Random();
            // 1. Chọn ngẫu nhiên danh mục mục tiêu
            string targetCategory = _categories[rand.Next(_categories.Length)];
            string prompt = _prompts[targetCategory];

            // Đường dẫn gốc tới các thư mục chứa ảnh
            string webRootPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot");
            string categoriesPath = Path.Combine(webRootPath, "assets", "categories");

            // Đảm bảo các thư mục tồn tại
            foreach (var cat in _categories)
            {
                var dir = Path.Combine(categoriesPath, cat);
                if (!Directory.Exists(dir))
                {
                    Directory.CreateDirectory(dir);
                }
            }

            // Đọc danh sách ảnh từ danh mục mục tiêu
            var targetImages = GetImagesFromFolder(categoriesPath, targetCategory);
            // Đọc danh sách ảnh từ các danh mục gây nhiễu (distractors)
            var distractorImages = new List<string>();
            foreach (var cat in _categories.Where(c => c != targetCategory))
            {
                distractorImages.AddRange(GetImagesFromFolder(categoriesPath, cat));
            }

            // Đề phòng trường hợp chưa có ảnh trong thư mục (tạo ảnh giả lập)
            if (targetImages.Count == 0 || distractorImages.Count == 0)
            {
                return GeneratePlaceholderChallenge(targetCategory, prompt, baseRequestUrl);
            }

            // Chọn ngẫu nhiên 3 đến 4 ảnh mục tiêu
            int numTarget = rand.Next(3, 5); // 3 hoặc 4
            numTarget = Math.Min(numTarget, targetImages.Count);
            var selectedTargets = targetImages.OrderBy(x => rand.Next()).Take(numTarget).ToList();

            // Chọn ngẫu nhiên (9 - numTarget) ảnh gây nhiễu
            int numDistractors = 9 - selectedTargets.Count;
            var selectedDistractors = distractorImages.OrderBy(x => rand.Next()).Take(numDistractors).ToList();

            // Gộp và trộn ngẫu nhiên (Shuffle)
            var allSelected = selectedTargets.Select(img => new { Path = img, IsTarget = true })
                .Concat(selectedDistractors.Select(img => new { Path = img, IsTarget = false }))
                .OrderBy(x => rand.Next())
                .ToList();

            var challengeResult = new ImageGridChallengeResult
            {
                TargetCategory = targetCategory,
                PromptText = prompt
            };

            for (int i = 0; i < allSelected.Count; i++)
            {
                var item = allSelected[i];
                // Chuyển đường dẫn vật lý thành URL tương đối (relative web URL)
                string relativeUrl = item.Path.Replace(webRootPath, "").Replace("\\", "/").TrimStart('/');
                string fullUrl = $"{baseRequestUrl.TrimEnd('/')}/{relativeUrl}";

                challengeResult.Images.Add(new GridImageItem
                {
                    Index = i,
                    ImageUrl = fullUrl
                });

                if (item.IsTarget)
                {
                    challengeResult.CorrectIndices.Add(i);
                }
            }

            return challengeResult;
        }

        private List<string> GetImagesFromFolder(string rootPath, string folderName)
        {
            var folder = Path.Combine(rootPath, folderName);
            if (!Directory.Exists(folder))
            {
                return new List<string>();
            }

            var allowedExtensions = new[] { ".jpg", ".jpeg", ".png", ".gif", ".webp" };
            return Directory.GetFiles(folder)
                .Where(file => allowedExtensions.Contains(Path.GetExtension(file).ToLower()))
                .ToList();
        }

        // Tạo challenge giả lập tự vẽ (Placeholder) nếu không tìm thấy tệp ảnh nào trong đĩa cứng
        private ImageGridChallengeResult GeneratePlaceholderChallenge(string targetCategory, string prompt, string baseRequestUrl)
        {
            var rand = new Random();
            var challengeResult = new ImageGridChallengeResult
            {
                TargetCategory = targetCategory,
                PromptText = prompt
            };

            int numTarget = rand.Next(3, 5); // 3 hoặc 4
            var targetIndices = new HashSet<int>();
            while (targetIndices.Count < numTarget)
            {
                targetIndices.Add(rand.Next(9));
            }

            for (int i = 0; i < 9; i++)
            {
                bool isTarget = targetIndices.Contains(i);
                // Dùng dịch vụ online Unsplash/via.placeholder hoặc ảnh mẫu cục bộ
                // Để đảm bảo bộ giải AI (Python) chạy độc lập được, ta sẽ dùng ảnh Unsplash có nhãn từ khóa
                string categoryKeyword = isTarget ? targetCategory : _categories.First(c => c != targetCategory);
                // Tạo ảnh có kích thước 150x150 kèm chữ để dễ kiểm tra
                string imageUrl = $"https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=150&q=80"; // fallback

                // Hoặc sinh URL mẫu dạng: http://localhost:5097/assets/categories/placeholder_{category}_{random}.png
                challengeResult.Images.Add(new GridImageItem
                {
                    Index = i,
                    ImageUrl = imageUrl
                });

                if (isTarget)
                {
                    challengeResult.CorrectIndices.Add(i);
                }
            }

            return challengeResult;
        }
    }
}
