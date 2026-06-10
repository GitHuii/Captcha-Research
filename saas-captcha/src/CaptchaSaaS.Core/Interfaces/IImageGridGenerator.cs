using System.Collections.Generic;

namespace CaptchaSaaS.Core.Interfaces
{
    public class ImageGridChallengeResult
    {
        public string TargetCategory { get; set; } = string.Empty; // e.g. "car", "dog", "cat", "tree"
        public string PromptText { get; set; } = string.Empty; // e.g. "Xe hơi", "Chó", "Mèo", "Cây cối"
        public List<GridImageItem> Images { get; set; } = new List<GridImageItem>();
        public List<int> CorrectIndices { get; set; } = new List<int>();
    }

    public class GridImageItem
    {
        public int Index { get; set; }
        public string ImageUrl { get; set; } = string.Empty;
    }

    public interface IImageGridGenerator
    {
        ImageGridChallengeResult GenerateChallenge(string baseRequestUrl);
    }
}
