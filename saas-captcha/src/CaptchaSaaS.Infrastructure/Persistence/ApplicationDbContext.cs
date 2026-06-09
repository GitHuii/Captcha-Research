using Microsoft.EntityFrameworkCore;
using CaptchaSaaS.Core.Entities;

namespace CaptchaSaaS.Infrastructure.Persistence
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }

        public DbSet<User> Users { get; set; } = null!;
        public DbSet<Website> Websites { get; set; } = null!;
        public DbSet<CaptchaChallenge> CaptchaChallenges { get; set; } = null!;

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // User configuration
            modelBuilder.Entity<User>(entity =>
            {
                entity.ToTable("Users");
                entity.HasKey(e => e.Id);
                entity.Property(e => e.Email).IsRequired().HasMaxLength(256);
                entity.HasIndex(e => e.Email).IsUnique();
                entity.Property(e => e.PasswordHash).IsRequired();
            });

            // Website configuration
            modelBuilder.Entity<Website>(entity =>
            {
                entity.ToTable("Websites");
                entity.HasKey(e => e.Id);
                entity.Property(e => e.Domain).IsRequired().HasMaxLength(256);
                entity.Property(e => e.SiteKey).IsRequired().HasMaxLength(128);
                entity.HasIndex(e => e.SiteKey).IsUnique();
                entity.Property(e => e.SecretKey).IsRequired().HasMaxLength(128);

                entity.HasOne(d => d.User)
                    .WithMany(p => p.Websites)
                    .HasForeignKey(d => d.UserId)
                    .OnDelete(DeleteBehavior.Cascade);
            });

            // CaptchaChallenge configuration
            modelBuilder.Entity<CaptchaChallenge>(entity =>
            {
                entity.ToTable("CaptchaChallenges");
                entity.HasKey(e => e.Id);
                entity.Property(e => e.Solution).IsRequired().HasMaxLength(4);
                entity.Property(e => e.ImagePath).IsRequired().HasMaxLength(512);
                entity.Property(e => e.Status).HasConversion<string>().HasMaxLength(32);

                entity.HasOne(d => d.Website)
                    .WithMany(p => p.Challenges)
                    .HasForeignKey(d => d.WebsiteId)
                    .OnDelete(DeleteBehavior.Cascade);
            });
        }
    }
}
