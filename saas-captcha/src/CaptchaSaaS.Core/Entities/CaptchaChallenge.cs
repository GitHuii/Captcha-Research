using System;

namespace CaptchaSaaS.Core.Entities
{
    public class CaptchaChallenge
    {
        public Guid Id { get; set; } = Guid.NewGuid();
        public Guid WebsiteId { get; set; }
        public string Solution { get; set; } = string.Empty;
        public string ImagePath { get; set; } = string.Empty;
        public string? BlockImagePath { get; set; }
        public int YOffset { get; set; } = 0;
        public CaptchaType Type { get; set; } = CaptchaType.TextV1;
        public ChallengeStatus Status { get; set; } = ChallengeStatus.Pending;
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime ExpiresAt { get; set; }

        // Navigation property
        public Website Website { get; set; } = null!;
    }
}
