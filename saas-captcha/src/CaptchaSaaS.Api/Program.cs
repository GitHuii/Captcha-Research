using Microsoft.EntityFrameworkCore;
using CaptchaSaaS.Infrastructure.Persistence;
using CaptchaSaaS.Core.Interfaces;
using CaptchaSaaS.Core.Services;
using CaptchaSaaS.Infrastructure.Services;
using System.IO;

var builder = WebApplication.CreateBuilder(args);

// Đăng ký Controllers
builder.Services.AddControllers();

// Đăng ký Swagger/OpenAPI
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Cấu hình DbContext kết nối SQL Server
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

// Đăng ký Dependency Injection
builder.Services.AddTransient<ICaptchaGenerator, CaptchaGenerator>();
builder.Services.AddTransient<ISliderCaptchaGenerator, SliderCaptchaGenerator>();
builder.Services.AddTransient<ISliderTrajectoryValidator, SliderTrajectoryValidator>();
builder.Services.AddTransient<IFileStorageService, FileStorageService>();

// Cấu hình CORS để các website khác có thể nhúng widget gọi API
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

app.UseHttpsRedirection();

// Kích hoạt Swagger UI
app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "CaptchaSaaS API v1");
    c.RoutePrefix = string.Empty; // Hiển thị Swagger UI tại root http://localhost:5097/
});

// Cho phép phục vụ file tĩnh (ảnh captcha trong thư mục wwwroot)
app.UseStaticFiles();

// Tạo thư mục wwwroot nếu chưa tồn tại để tránh lỗi
var wwwrootPath = Path.Combine(app.Environment.ContentRootPath, "wwwroot");
if (!Directory.Exists(wwwrootPath))
{
    Directory.CreateDirectory(wwwrootPath);
}

app.UseCors("AllowAll");

app.UseAuthorization();

app.MapControllers();

app.Run();
