using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using CaptchaSaaS.Infrastructure.Persistence;
using CaptchaSaaS.Core.Entities;
using CaptchaSaaS.Core.Interfaces;
using Microsoft.Extensions.Configuration;
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

namespace CaptchaSaaS.Api.Controllers
{
    [ApiController]
    [Route("api/v2/captcha")]
    public class CaptchaV2Controller : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly ISliderCaptchaGenerator _sliderCaptchaGenerator;
        private readonly ISliderTrajectoryValidator _sliderTrajectoryValidator;
        private readonly IFileStorageService _fileStorageService;
        private readonly int _expirationMinutes;

        public CaptchaV2Controller(
            ApplicationDbContext context,
            ISliderCaptchaGenerator sliderCaptchaGenerator,
            ISliderTrajectoryValidator sliderTrajectoryValidator,
            IFileStorageService fileStorageService,
            IConfiguration configuration)
        {
            _context = context;
            _sliderCaptchaGenerator = sliderCaptchaGenerator;
            _sliderTrajectoryValidator = sliderTrajectoryValidator;
            _fileStorageService = fileStorageService;
            
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

            var challengeId = Guid.NewGuid();

            try
            {
                // 1. Sinh ảnh Slider Captcha (ảnh nền đã khoét lỗ và mảnh ghép)
                var (xTarget, yOffset, bgBytes, blockBytes) = _sliderCaptchaGenerator.Generate();

                // 2. Lưu ảnh vật lý
                var bgFileName = $"{challengeId}_bg.png";
                var blockFileName = $"{challengeId}_block.png";

                var bgRelativePath = await _fileStorageService.SaveImageAsync(bgBytes, bgFileName);
                var blockRelativePath = await _fileStorageService.SaveImageAsync(blockBytes, blockFileName);

                // 3. Lưu thông tin vào Database SQL Server
                var challenge = new CaptchaChallenge
                {
                    Id = challengeId,
                    WebsiteId = website.Id,
                    Solution = xTarget.ToString("F2"), // Lưu tọa độ X dưới dạng chuỗi số thực
                    ImagePath = bgRelativePath,
                    BlockImagePath = blockRelativePath,
                    YOffset = yOffset,
                    Type = CaptchaType.SliderV2,
                    Status = ChallengeStatus.Pending,
                    CreatedAt = DateTime.UtcNow,
                    ExpiresAt = DateTime.UtcNow.AddMinutes(_expirationMinutes)
                };

                _context.CaptchaChallenges.Add(challenge);
                await _context.SaveChangesAsync();

                // 4. Trả về thông tin thử thách
                var base64Bg = Convert.ToBase64String(bgBytes);
                var base64Block = Convert.ToBase64String(blockBytes);
                var bgUrl = $"{Request.Scheme}://{Request.Host}/{bgRelativePath}";
                var blockUrl = $"{Request.Scheme}://{Request.Host}/{blockRelativePath}";

                return Ok(new
                {
                    success = true,
                    challengeId,
                    yOffset,
                    bgUrl,
                    blockUrl,
                    bgImage = $"data:image/png;base64,{base64Bg}",
                    blockImage = $"data:image/png;base64,{base64Block}"
                });
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { success = false, error = $"Failed to generate challenge: {ex.Message}" });
            }
        }

        [HttpPost("verify")]
        public async Task<IActionResult> Verify([FromBody] VerifyV2Request request)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.SecretKey))
            {
                return BadRequest(new { success = false, error = "SecretKey and ChallengeId are required." });
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

            // 4. Kiểm tra loại Captcha
            if (challenge.Type != CaptchaType.SliderV2)
            {
                return BadRequest(new { success = false, error = "This is not a Slider V2 challenge." });
            }

            // 5. Xác thực tọa độ X (sai lệch tối đa cho phép là 4px)
            if (!double.TryParse(challenge.Solution, out double xTarget))
            {
                return StatusCode(500, new { success = false, error = "Invalid solution in database." });
            }

            double xDiff = Math.Abs(request.XOffset - xTarget);
            bool isCorrectPos = xDiff <= 4.0;

            if (!isCorrectPos)
            {
                challenge.Status = ChallengeStatus.Expired; // Thất bại làm hết hạn thử thách luôn
                await _context.SaveChangesAsync();
                return Ok(new { success = false, error = $"Incorrect position. Diff: {xDiff:F2}px." });
            }

            // 6. Phân tích quỹ đạo chuyển động chuột để chặn Bot
            // Nếu người dùng không gửi quỹ đạo (hoặc gửi trống), coi như không hợp lệ
            if (request.Trajectory == null || request.Trajectory.Count == 0)
            {
                challenge.Status = ChallengeStatus.Expired;
                await _context.SaveChangesAsync();
                return Ok(new { success = false, error = "Verification failed: Missing drag trajectory data." });
            }

            // Map VerifyV2Request.Trajectory sang TrajectoryPointV2 của core
            var coreTrajectory = new List<TrajectoryPointV2>();
            foreach (var pt in request.Trajectory)
            {
                coreTrajectory.Add(new TrajectoryPointV2 { X = pt.X, Y = pt.Y, T = pt.T });
            }

            bool isHuman = _sliderTrajectoryValidator.Validate(coreTrajectory, out string rejectReason);

            if (!isHuman)
            {
                challenge.Status = ChallengeStatus.Expired;
                await _context.SaveChangesAsync();
                return Ok(new { success = false, error = $"Bot detected! Reason: {rejectReason}" });
            }

            // Hợp lệ hoàn toàn
            challenge.Status = ChallengeStatus.Verified;
            await _context.SaveChangesAsync();

            return Ok(new { success = true });
        }
    }

    public class VerifyV2Request
    {
        public string SecretKey { get; set; } = string.Empty;
        public Guid ChallengeId { get; set; }
        public double XOffset { get; set; }
        public List<VerifyV2TrajectoryPoint> Trajectory { get; set; } = new List<VerifyV2TrajectoryPoint>();
    }

    public class VerifyV2TrajectoryPoint
    {
        public double X { get; set; }
        public double Y { get; set; }
        public long T { get; set; }
    }
}
