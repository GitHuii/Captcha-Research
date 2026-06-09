using System;
using System.IO;
using System.Threading.Tasks;
using CaptchaSaaS.Core.Interfaces;
using Microsoft.Extensions.Configuration;

namespace CaptchaSaaS.Infrastructure.Services
{
    public class FileStorageService : IFileStorageService
    {
        private readonly string _uploadDirectory;

        public FileStorageService(IConfiguration configuration)
        {
            // Đọc đường dẫn từ configuration, mặc định là wwwroot/uploads/captchas
            var configuredPath = configuration["StorageSettings:UploadDirectory"];
            
            if (string.IsNullOrWhiteSpace(configuredPath))
            {
                _uploadDirectory = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "uploads", "captchas");
            }
            else
            {
                _uploadDirectory = Path.IsPathRooted(configuredPath) 
                    ? configuredPath 
                    : Path.Combine(Directory.GetCurrentDirectory(), configuredPath);
            }
        }

        public async Task<string> SaveImageAsync(byte[] imageBytes, string fileName)
        {
            if (!Directory.Exists(_uploadDirectory))
            {
                Directory.CreateDirectory(_uploadDirectory);
            }

            var filePath = Path.Combine(_uploadDirectory, fileName);
            await File.WriteAllBytesAsync(filePath, imageBytes);
            
            // Trả về đường dẫn relative để web client có thể truy cập qua URL (ví dụ: uploads/captchas/filename.png)
            return Path.Combine("uploads", "captchas", fileName).Replace("\\", "/");
        }

        public Task DeleteImageAsync(string filePath)
        {
            // Tìm đường dẫn tuyệt đối để xóa
            var absolutePath = Path.IsPathRooted(filePath) 
                ? filePath 
                : Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", filePath.TrimStart('/'));

            if (File.Exists(absolutePath))
            {
                File.Delete(absolutePath);
            }
            return Task.CompletedTask;
        }
    }
}
