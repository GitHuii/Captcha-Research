namespace CaptchaSaaS.Core.Interfaces
{
    public interface ICaptchaGenerator
    {
        /// <summary>
        /// Generates a captcha text and its corresponding image as a byte array.
        /// </summary>
        /// <param name="length">Length of the captcha text (default is 4)</param>
        /// <returns>A tuple containing the generated text and the image byte array.</returns>
        (string Text, byte[] ImageBytes) Generate(int length = 4);
    }
}
