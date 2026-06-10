using System;
using System.Collections.Generic;
using System.Linq;
using CaptchaSaaS.Core.Interfaces;

namespace CaptchaSaaS.Core.Services
{
    public class SliderTrajectoryValidator : ISliderTrajectoryValidator
    {
        public bool Validate(List<TrajectoryPointV2> trajectory, out string reason)
        {
            reason = string.Empty;

            // 1. Kiểm tra nếu không có dữ liệu quỹ đạo hoặc quá ít điểm
            if (trajectory == null || trajectory.Count < 5)
            {
                reason = "Too few trajectory points (potentially automated jump).";
                return false;
            }

            // Sắp xếp các điểm theo thời gian tăng dần
            var sortedPoints = trajectory.OrderBy(p => p.T).ToList();

            // 2. Kiểm tra tổng thời gian kéo
            long startTime = sortedPoints.First().T;
            long endTime = sortedPoints.Last().T;
            long totalDuration = endTime - startTime;

            if (totalDuration < 200) // Dưới 200ms
            {
                reason = $"Slider solved too fast ({totalDuration}ms). Likely a bot.";
                return false;
            }

            if (totalDuration > 15000) // Kéo quá 15 giây
            {
                reason = $"Slider took too long ({totalDuration}ms). Session expired.";
                return false;
            }

            // 3. Kiểm tra chuyển động trục Y (con người kéo chuột tay luôn rung lắc nhẹ)
            var yCoordinates = sortedPoints.Select(p => p.Y).ToList();
            double meanY = yCoordinates.Average();
            double sumOfSquaresY = yCoordinates.Sum(y => Math.Pow(y - meanY, 2));
            double stdDevY = Math.Sqrt(sumOfSquaresY / yCoordinates.Count);

            // Nếu kéo một đường thẳng tuyệt đối (stdDevY = 0 hoặc rất bé < 0.05), khả năng cao là bot
            if (stdDevY < 0.05)
            {
                reason = "Perfect straight horizontal line detected (no human hand tremor).";
                return false;
            }

            // 4. Kiểm tra sự thay đổi của vận tốc (vận tốc biến thiên vs vận tốc không đổi của bot)
            var velocities = new List<double>();
            for (int i = 1; i < sortedPoints.Count; i++)
            {
                var p1 = sortedPoints[i - 1];
                var p2 = sortedPoints[i];
                double dt = p2.T - p1.T;
                if (dt > 0)
                {
                    double dx = p2.X - p1.X;
                    double dy = p2.Y - p1.Y;
                    double dist = Math.Sqrt(dx * dx + dy * dy);
                    velocities.Add(dist / dt); // px per ms
                }
            }

            if (velocities.Count > 2)
            {
                double meanV = velocities.Average();
                double sumOfSquaresV = velocities.Sum(v => Math.Pow(v - meanV, 2));
                double stdDevV = Math.Sqrt(sumOfSquaresV / velocities.Count);

                // Nếu vận tốc không đổi (stdDevV rất bé), chứng tỏ kéo tự động bằng máy
                if (stdDevV < 0.01)
                {
                    reason = "Constant drag velocity detected (likely programmatic movement).";
                    return false;
                }
            }

            return true;
        }
    }
}
