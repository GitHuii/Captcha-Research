using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using CaptchaSaaS.Infrastructure.Persistence;
using CaptchaSaaS.Core.Entities;
using CaptchaSaaS.Core.Interfaces;
using Microsoft.Extensions.Configuration;
using System;
using System.IO;
using System.Threading.Tasks;

namespace CaptchaSaaS.Api.Controllers
{
    [ApiController]
    [Route("api/v1/captcha")]
    public class CaptchaController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly ICaptchaGenerator _captchaGenerator;
        private readonly IFileStorageService _fileStorageService;
        private readonly int _expirationMinutes;

        public CaptchaController(
            ApplicationDbContext context,
            ICaptchaGenerator captchaGenerator,
            IFileStorageService fileStorageService,
            IConfiguration configuration)
        {
            _context = context;
            _captchaGenerator = captchaGenerator;
            _fileStorageService = fileStorageService;
            
            // Đọc thời gian hết hạn captcha từ config, mặc định là 3 phút
            _expirationMinutes = configuration.GetValue<int>("CaptchaSettings:ExpirationMinutes", 3);
        }

        [HttpGet("challenge")]
        public async Task<IActionResult> GetChallenge([FromQuery] string siteKey)
        {
            if (string.IsNullOrWhiteSpace(siteKey))
            {
                return BadRequest(new { success = false, error = "SiteKey is required." });
            }

            var website = await _context.Websites.FirstOrDefaultAsync(w => w.SiteKey == siteKey);
            if (website == null)
            {
                return BadRequest(new { success = false, error = "Invalid SiteKey." });
            }

            // 1. Tạo captcha ngẫu nhiên (4 ký tự)
            var challengeId = Guid.NewGuid();
            var (text, imageBytes) = _captchaGenerator.Generate(4);

            // 2. Lưu ảnh vật lý dạng PNG
            var fileName = $"{challengeId}.png";
            var relativePath = await _fileStorageService.SaveImageAsync(imageBytes, fileName);

            // 3. Lưu thông tin challenge vào database SQL Server
            var challenge = new CaptchaChallenge
            {
                Id = challengeId,
                WebsiteId = website.Id,
                Solution = text,
                ImagePath = relativePath,
                Status = ChallengeStatus.Pending,
                CreatedAt = DateTime.UtcNow,
                ExpiresAt = DateTime.UtcNow.AddMinutes(_expirationMinutes)
            };

            _context.CaptchaChallenges.Add(challenge);
            await _context.SaveChangesAsync();

            // 4. Trả về challengeId, đường dẫn URL truy cập ảnh và dữ liệu dạng Base64
            var base64Image = Convert.ToBase64String(imageBytes);
            var imageUrl = $"{Request.Scheme}://{Request.Host}/{relativePath}";

            return Ok(new
            {
                success = true,
                challengeId,
                imageUrl,
                image = $"data:image/png;base64,{base64Image}"
            });
        }

        [HttpPost("verify")]
        public async Task<IActionResult> Verify([FromBody] VerifyRequest request)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.SecretKey) || string.IsNullOrWhiteSpace(request.Response))
            {
                return BadRequest(new { success = false, error = "SecretKey, ChallengeId and Response are required." });
            }

            // 1. Xác thực SecretKey của website
            var website = await _context.Websites.FirstOrDefaultAsync(w => w.SecretKey == request.SecretKey);
            if (website == null)
            {
                return BadRequest(new { success = false, error = "Invalid SecretKey." });
            }

            // 2. Tìm challenge tương ứng
            var challenge = await _context.CaptchaChallenges.FindAsync(request.ChallengeId);
            if (challenge == null || challenge.WebsiteId != website.Id)
            {
                return NotFound(new { success = false, error = "Challenge not found or does not belong to this website." });
            }

            // 3. Kiểm tra xem challenge đã được dùng hoặc hết hạn chưa
            if (challenge.Status != ChallengeStatus.Pending)
            {
                return Ok(new { success = false, error = $"Challenge already processed. Current status: {challenge.Status}" });
            }

            if (DateTime.UtcNow > challenge.ExpiresAt)
            {
                challenge.Status = ChallengeStatus.Expired;
                await _context.SaveChangesAsync();
                return Ok(new { success = false, error = "Challenge has expired." });
            }

            // 4. So khớp kết quả (không phân biệt hoa thường)
            bool isCorrect = string.Equals(challenge.Solution.Trim(), request.Response.Trim(), StringComparison.OrdinalIgnoreCase);

            // Một challenge chỉ được verify 1 lần duy nhất (thành công -> Verified, thất bại -> Expired)
            challenge.Status = isCorrect ? ChallengeStatus.Verified : ChallengeStatus.Expired;
            await _context.SaveChangesAsync();

            if (isCorrect)
            {
                return Ok(new { success = true });
            }
            else
            {
                return Ok(new { success = false, error = "Incorrect solution." });
            }
        }
    }

    public class VerifyRequest
    {
        public string SecretKey { get; set; } = string.Empty;
        public Guid ChallengeId { get; set; }
        public string Response { get; set; } = string.Empty;
    }
}
