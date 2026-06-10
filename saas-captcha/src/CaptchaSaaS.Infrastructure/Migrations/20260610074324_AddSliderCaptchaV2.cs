using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace CaptchaSaaS.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddSliderCaptchaV2 : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AlterColumn<string>(
                name: "Solution",
                table: "CaptchaChallenges",
                type: "nvarchar(64)",
                maxLength: 64,
                nullable: false,
                oldClrType: typeof(string),
                oldType: "nvarchar(4)",
                oldMaxLength: 4);

            migrationBuilder.AddColumn<string>(
                name: "BlockImagePath",
                table: "CaptchaChallenges",
                type: "nvarchar(512)",
                maxLength: 512,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "Type",
                table: "CaptchaChallenges",
                type: "nvarchar(32)",
                maxLength: 32,
                nullable: false,
                defaultValue: "TextV1");

            migrationBuilder.AddColumn<int>(
                name: "YOffset",
                table: "CaptchaChallenges",
                type: "int",
                nullable: false,
                defaultValue: 0);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "BlockImagePath",
                table: "CaptchaChallenges");

            migrationBuilder.DropColumn(
                name: "Type",
                table: "CaptchaChallenges");

            migrationBuilder.DropColumn(
                name: "YOffset",
                table: "CaptchaChallenges");

            migrationBuilder.AlterColumn<string>(
                name: "Solution",
                table: "CaptchaChallenges",
                type: "nvarchar(4)",
                maxLength: 4,
                nullable: false,
                oldClrType: typeof(string),
                oldType: "nvarchar(64)",
                oldMaxLength: 64);
        }
    }
}
