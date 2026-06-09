using System;
using System.Collections.Generic;

namespace CaptchaSaaS.Core.Entities
{
    public class Website
    {
        public Guid Id { get; set; } = Guid.NewGuid();
        public Guid UserId { get; set; }
        public string Domain { get; set; } = string.Empty;
        public string SiteKey { get; set; } = string.Empty;
        public string SecretKey { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        // Navigation properties
        public User User { get; set; } = null!;
        public ICollection<CaptchaChallenge> Challenges { get; set; } = new List<CaptchaChallenge>();
    }
}
