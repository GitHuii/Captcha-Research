using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using CaptchaSaaS.Infrastructure.Persistence;
using CaptchaSaaS.Core.Entities;
using CaptchaSaaS.Core.Interfaces;
using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Threading.Tasks;

namespace CaptchaSaaS.Api.Controllers
{
    [ApiController]
    [Route("api/v1/dataset")]
    public class DatasetController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly ICaptchaGenerator _captchaGenerator;
        private readonly IFileStorageService _fileStorageService;

        public DatasetController(
            ApplicationDbContext context,
            ICaptchaGenerator captchaGenerator,
            IFileStorageService fileStorageService)
        {
            _context = context;
            _captchaGenerator = captchaGenerator;
            _fileStorageService = fileStorageService;
        }

        [HttpGet("generate")]
        public async Task<IActionResult> GenerateDataset([FromQuery] int count = 100, [FromQuery] string? siteKey = null)
        {
            if (count <= 0 || count > 5000)
            {
                return BadRequest(new { success = false, error = "Count must be between 1 and 5000." });
            }

            Website? website = null;
            if (string.IsNullOrEmpty(siteKey))
            {
                // Nếu không truyền siteKey, lấy website đầu tiên trong DB để gán
                website = await _context.Websites.FirstOrDefaultAsync();
            }
            else
            {
                website = await _context.Websites.FirstOrDefaultAsync(w => w.SiteKey == siteKey);
            }

            if (website == null)
            {
                return BadRequest(new { success = false, error = "No registered website found. Please register a website via Portal API first." });
            }

            int generated = 0;
            for (int i = 0; i < count; i++)
            {
                var challengeId = Guid.NewGuid();
                var (text, imageBytes) = _captchaGenerator.Generate(4);
                
                var fileName = $"{challengeId}.png";
                var relativePath = await _fileStorageService.SaveImageAsync(imageBytes, fileName);

                var challenge = new CaptchaChallenge
                {
                    Id = challengeId,
                    WebsiteId = website.Id,
                    Solution = text,
                    ImagePath = relativePath,
                    Status = ChallengeStatus.Pending,
                    CreatedAt = DateTime.UtcNow,
                    // Dữ liệu dùng để train AI sẽ cấu hình hết hạn xa để dễ kiểm thử
                    ExpiresAt = DateTime.UtcNow.AddYears(1) 
                };

                _context.CaptchaChallenges.Add(challenge);
                generated++;
            }

            await _context.SaveChangesAsync();
            return Ok(new { success = true, message = $"Successfully generated {generated} captcha images.", totalGenerated = generated });
        }

        [HttpGet("export")]
        public async Task<IActionResult> ExportDataset()
        {
            var challenges = await _context.CaptchaChallenges.ToListAsync();
            if (challenges.Count == 0)
            {
                return NotFound(new { success = false, error = "No captcha challenges found in the database. Please generate some first." });
            }

            var memoryStream = new MemoryStream();
            
            // Dùng using để giải phóng ZipArchive trước khi trả về stream
            using (var archive = new ZipArchive(memoryStream, ZipArchiveMode.Create, true))
            {
                var csvBuilder = new StringBuilder();
                csvBuilder.AppendLine("image_name,label");

                foreach (var challenge in challenges)
                {
                    var fileName = Path.GetFileName(challenge.ImagePath);
                    csvBuilder.AppendLine($"{fileName},{challenge.Solution}");

                    var absolutePath = Path.IsPathRooted(challenge.ImagePath) 
                        ? challenge.ImagePath 
                        : Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", challenge.ImagePath.TrimStart('/'));

                    if (System.IO.File.Exists(absolutePath))
                    {
                        var entry = archive.CreateEntry($"images/{fileName}");
                        using (var entryStream = entry.Open())
                        using (var fileStream = new FileStream(absolutePath, FileMode.Open, FileAccess.Read))
                        {
                            await fileStream.CopyToAsync(entryStream);
                        }
                    }
                }

                // Ghi file dataset.csv vào file zip
                var csvEntry = archive.CreateEntry("dataset.csv");
                using (var writer = new StreamWriter(csvEntry.Open()))
                {
                    await writer.WriteAsync(csvBuilder.ToString());
                }
            }

            memoryStream.Seek(0, SeekOrigin.Begin);
            return base.File(memoryStream, "application/zip", "captcha_dataset.zip");
        }
    }
}
