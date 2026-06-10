using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using CaptchaSaaS.Infrastructure.Persistence;
using CaptchaSaaS.Core.Entities;
using CaptchaSaaS.Core.Interfaces;
using Microsoft.Extensions.Configuration;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace CaptchaSaaS.Api.Controllers
{
    [ApiController]
    [Route("api/v3/captcha")]
    public class CaptchaV3Controller : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly IBehavioralValidator _behavioralValidator;
        private readonly IImageGridGenerator _imageGridGenerator;
        private readonly int _expirationMinutes;

        public CaptchaV3Controller(
            ApplicationDbContext context,
            IBehavioralValidator behavioralValidator,
            IImageGridGenerator imageGridGenerator,
            IConfiguration configuration)
        {
            _context = context;
            _behavioralValidator = behavioralValidator;
            _imageGridGenerator = imageGridGenerator;
            _expirationMinutes = configuration.GetValue<int>("CaptchaSettings:ExpirationMinutes", 3);
        }

        [HttpPost("verify-behavior")]
        public async Task<IActionResult> VerifyBehavior([FromBody] VerifyBehaviorRequest request)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.SiteKey))
            {
                return BadRequest(new { success = false, error = "SiteKey is required." });
            }

            var website = await _context.Websites.FirstOrDefaultAsync(w => w.SiteKey == request.SiteKey);
            if (website == null)
            {
                return BadRequest(new { success = false, error = "Invalid SiteKey." });
            }

            // 1. Chấm điểm hành vi
            var evalResult = _behavioralValidator.Evaluate(request.Telemetry);

            var challengeId = Guid.NewGuid();

            if (!evalResult.IsBot)
            {
                // Hành vi tốt -> Ghi nhận và duyệt luôn
                var challenge = new CaptchaChallenge
                {
                    Id = challengeId,
                    WebsiteId = website.Id,
                    Solution = evalResult.Score.ToString("F2"),
                    ImagePath = "behavior_pass",
                    Type = CaptchaType.BehavioralV3,
                    Status = ChallengeStatus.Verified, // Verified trực tiếp!
                    CreatedAt = DateTime.UtcNow,
                    ExpiresAt = DateTime.UtcNow.AddMinutes(_expirationMinutes)
                };

                _context.CaptchaChallenges.Add(challenge);
                await _context.SaveChangesAsync();

                return Ok(new
                {
                    success = true,
                    score = evalResult.Score,
                    challengeId = challengeId,
                    requireFallback = false
                });
            }
            else
            {
                // Điểm thấp -> Sinh thử thách chọn ảnh dự phòng (fallback)
                // Lấy URL gốc của server để sinh đường dẫn ảnh tuyệt đối cho client
                string baseRequestUrl = $"{Request.Scheme}://{Request.Host}";
                var gridChallenge = _imageGridGenerator.GenerateChallenge(baseRequestUrl);

                var challenge = new CaptchaChallenge
                {
                    Id = challengeId,
                    WebsiteId = website.Id,
                    // Lưu các index đúng cách nhau bởi dấu phẩy, ví dụ: "0,3,7"
                    Solution = string.Join(",", gridChallenge.CorrectIndices),
                    ImagePath = $"grid_{gridChallenge.TargetCategory}", // Lưu metadata category
                    Type = CaptchaType.ImageGridV3,
                    Status = ChallengeStatus.Pending, // Chờ giải quyết
                    CreatedAt = DateTime.UtcNow,
                    ExpiresAt = DateTime.UtcNow.AddMinutes(_expirationMinutes)
                };

                _context.CaptchaChallenges.Add(challenge);
                await _context.SaveChangesAsync();

                return Ok(new
                {
                    success = false,
                    score = evalResult.Score,
                    reasons = evalResult.Reasons,
                    requireFallback = true,
                    challengeId = challengeId,
                    promptText = gridChallenge.PromptText,
                    targetCategory = gridChallenge.TargetCategory,
                    images = gridChallenge.Images
                });
            }
        }

        [HttpPost("verify-image")]
        public async Task<IActionResult> VerifyImage([FromBody] VerifyImageRequest request)
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

            if (challenge.Type != CaptchaType.ImageGridV3)
            {
                return BadRequest(new { success = false, error = "This is not an ImageGrid V3 challenge." });
            }

            // 4. So khớp kết quả
            // Đọc danh sách index đúng từ Database
            var correctIndices = challenge.Solution.Split(',', StringSplitOptions.RemoveEmptyEntries)
                .Select(int.Parse)
                .OrderBy(x => x)
                .ToList();

            var submittedIndices = (request.SelectedIndices ?? new List<int>())
                .OrderBy(x => x)
                .ToList();

            // So sánh hai danh sách có bằng nhau tuyệt đối
            bool isCorrect = correctIndices.SequenceEqual(submittedIndices);

            // Một challenge chỉ được verify 1 lần duy nhất (thành công -> Verified, thất bại -> Expired)
            challenge.Status = isCorrect ? ChallengeStatus.Verified : ChallengeStatus.Expired;
            await _context.SaveChangesAsync();

            if (isCorrect)
            {
                return Ok(new { success = true });
            }
            else
            {
                return Ok(new { success = false, error = "Incorrect image selection." });
            }
        }

        [HttpPost("verify")]
        public async Task<IActionResult> VerifyGeneral([FromBody] VerifyGeneralRequest request)
        {
            if (request == null || string.IsNullOrWhiteSpace(request.SecretKey))
            {
                return BadRequest(new { success = false, error = "SecretKey and ChallengeId are required." });
            }

            var website = await _context.Websites.FirstOrDefaultAsync(w => w.SecretKey == request.SecretKey);
            if (website == null)
            {
                return BadRequest(new { success = false, error = "Invalid SecretKey." });
            }

            var challenge = await _context.CaptchaChallenges.FindAsync(request.ChallengeId);
            if (challenge == null || challenge.WebsiteId != website.Id)
            {
                return NotFound(new { success = false, error = "Challenge not found." });
            }

            // Chỉ chấp nhận các challenge đã được giải và đánh dấu Verified
            if (challenge.Status == ChallengeStatus.Verified)
            {
                return Ok(new { success = true, type = challenge.Type.ToString(), solution = challenge.Solution });
            }

            return Ok(new { success = false, error = $"Challenge is not verified. Current status: {challenge.Status}" });
        }
    }

    public class VerifyBehaviorRequest
    {
        public string SiteKey { get; set; } = string.Empty;
        public BehavioralTelemetry Telemetry { get; set; } = new BehavioralTelemetry();
    }

    public class VerifyImageRequest
    {
        public string SecretKey { get; set; } = string.Empty;
        public Guid ChallengeId { get; set; }
        public List<int> SelectedIndices { get; set; } = new List<int>();
    }

    public class VerifyGeneralRequest
    {
        public string SecretKey { get; set; } = string.Empty;
        public Guid ChallengeId { get; set; }
    }
}
