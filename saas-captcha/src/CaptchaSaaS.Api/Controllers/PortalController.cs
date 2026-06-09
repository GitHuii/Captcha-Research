using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using CaptchaSaaS.Infrastructure.Persistence;
using CaptchaSaaS.Core.Entities;
using System;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Linq;

namespace CaptchaSaaS.Api.Controllers
{
    [ApiController]
    [Route("api/v1/portal")]
    public class PortalController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public PortalController(ApplicationDbContext context)
        {
            _context = context;
        }

        [HttpPost("users")]
        public async Task<IActionResult> CreateUser([FromBody] CreateUserRequest request)
        {
            if (string.IsNullOrWhiteSpace(request.Email) || string.IsNullOrWhiteSpace(request.Password))
            {
                return BadRequest("Email and Password are required.");
            }

            var emailNormalized = request.Email.Trim().ToLower();
            if (await _context.Users.AnyAsync(u => u.Email == emailNormalized))
            {
                return Conflict("User with this email already exists.");
            }

            var user = new User
            {
                Email = emailNormalized,
                PasswordHash = HashPassword(request.Password)
            };

            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            return Ok(new { user.Id, user.Email, user.CreatedAt });
        }

        [HttpPost("websites")]
        public async Task<IActionResult> RegisterWebsite([FromBody] RegisterWebsiteRequest request)
        {
            var user = await _context.Users.FindAsync(request.UserId);
            if (user == null)
            {
                return NotFound("User not found.");
            }

            if (string.IsNullOrWhiteSpace(request.Domain))
            {
                return BadRequest("Domain is required.");
            }

            var website = new Website
            {
                UserId = request.UserId,
                Domain = request.Domain.Trim().ToLower(),
                SiteKey = "sitekey_" + Guid.NewGuid().ToString("N"),
                SecretKey = "secretkey_" + Guid.NewGuid().ToString("N")
            };

            _context.Websites.Add(website);
            await _context.SaveChangesAsync();

            return Ok(new
            {
                website.Id,
                website.Domain,
                website.SiteKey,
                website.SecretKey,
                website.CreatedAt
            });
        }

        [HttpGet("websites/{userId}")]
        public async Task<IActionResult> GetWebsites(Guid userId)
        {
            var websites = await _context.Websites
                .Where(w => w.UserId == userId)
                .Select(w => new { w.Id, w.Domain, w.SiteKey, w.SecretKey, w.CreatedAt })
                .ToListAsync();

            return Ok(websites);
        }

        private static string HashPassword(string password)
        {
            byte[] bytes = SHA256.HashData(Encoding.UTF8.GetBytes(password));
            return Convert.ToHexString(bytes).ToLower();
        }
    }

    public record CreateUserRequest(string Email, string Password);
    public record RegisterWebsiteRequest(Guid UserId, string Domain);
}
