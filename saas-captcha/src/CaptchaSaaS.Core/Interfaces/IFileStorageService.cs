using System.Threading.Tasks;

namespace CaptchaSaaS.Core.Interfaces
{
    public interface IFileStorageService
    {
        /// <summary>
        /// Saves the image byte array to physical disk storage.
        /// </summary>
        /// <param name="imageBytes">The raw image byte array</param>
        /// <param name="fileName">Desired file name</param>
        /// <returns>The path or file name of the saved image</returns>
        Task<string> SaveImageAsync(byte[] imageBytes, string fileName);

        /// <summary>
        /// Deletes an image from disk storage.
        /// </summary>
        /// <param name="filePath">Path to the image to delete</param>
        Task DeleteImageAsync(string filePath);
    }
}
