namespace CaptchaSaaS.Core.Interfaces
{
    public interface ISliderCaptchaGenerator
    {
        /// <summary>
        /// Generates a slider captcha: background with a hole, puzzle piece, target X and Y offset.
        /// </summary>
        /// <returns>A tuple containing (XTarget, YOffset, BgImageBytes, BlockImageBytes)</returns>
        (double XTarget, int YOffset, byte[] BgImageBytes, byte[] BlockImageBytes) Generate();
    }
}
