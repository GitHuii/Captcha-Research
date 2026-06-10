using System;
using System.Collections.Generic;
using System.Linq;
using CaptchaSaaS.Core.Entities;
using CaptchaSaaS.Core.Interfaces;

namespace CaptchaSaaS.Core.Services
{
    public class BehavioralValidator : IBehavioralValidator
    {
        public BehavioralEvaluationResult Evaluate(BehavioralTelemetry telemetry)
        {
            var result = new BehavioralEvaluationResult
            {
                Score = 1.0,
                IsBot = false
            };

            if (telemetry == null)
            {
                result.Score = 0.0;
                result.IsBot = true;
                result.Reasons.Add("No telemetry data provided.");
                return result;
            }

            // 1. Kiểm tra Dấu vết Trình duyệt giả lập (Headless/Automation check)
            var fp = telemetry.Fingerprint;
            if (fp.Webdriver)
            {
                result.Score = 0.0;
                result.IsBot = true;
                result.Reasons.Add("Automation flag 'navigator.webdriver' is active.");
            }

            if (fp.IsHeadless)
            {
                result.Score = 0.0;
                result.IsBot = true;
                result.Reasons.Add("Client-side headless environment detected.");
            }

            if (!string.IsNullOrEmpty(fp.UserAgent))
            {
                var uaLower = fp.UserAgent.ToLower();
                if (uaLower.Contains("headlesschrome") || 
                    uaLower.Contains("puppeteer") || 
                    uaLower.Contains("playwright") || 
                    uaLower.Contains("selenium"))
                {
                    result.Score = 0.0;
                    result.IsBot = true;
                    result.Reasons.Add("Suspicious User-Agent string indicating automation.");
                }
            }

            // Nếu phát hiện trực tiếp dấu vết bot hệ thống thì dừng lại và chặn ngay
            if (result.IsBot)
            {
                return result;
            }

            double penalties = 0.0;

            // 2. Phân tích hành vi di chuyển chuột (Mouse Dynamics)
            var mouseActions = telemetry.MouseActions;
            if (mouseActions == null || mouseActions.Count < 5)
            {
                penalties += 0.4;
                result.Reasons.Add("Insufficient mouse interaction points.");
            }
            else
            {
                // Sắp xếp theo thời gian
                var sortedMouse = mouseActions.OrderBy(m => m.T).ToList();
                
                // Kiểm tra tốc độ di chuyển
                var velocities = new List<double>();
                var stepsY = new List<double>();
                
                for (int i = 1; i < sortedMouse.Count; i++)
                {
                    var p1 = sortedMouse[i - 1];
                    var p2 = sortedMouse[i];
                    double dt = p2.T - p1.T;
                    if (dt > 0)
                    {
                        double dx = p2.X - p1.X;
                        double dy = p2.Y - p1.Y;
                        double dist = Math.Sqrt(dx * dx + dy * dy);
                        velocities.Add(dist / dt); // px/ms
                        stepsY.Add(dy);
                    }
                }

                if (velocities.Count > 2)
                {
                    double meanV = velocities.Average();
                    double sumSqV = velocities.Sum(v => Math.Pow(v - meanV, 2));
                    double stdDevV = Math.Sqrt(sumSqV / velocities.Count);

                    // Độ lệch chuẩn của vận tốc bằng 0 hoặc quá bé -> Vận tốc không đổi (dấu hiệu của Bot)
                    if (stdDevV < 0.02)
                    {
                        penalties += 0.35;
                        result.Reasons.Add("Constant mouse movement velocity (unnatural).");
                    }
                }

                // Kiểm tra độ rung lắc tay (độ biến thiên trục Y)
                if (stepsY.Count > 2)
                {
                    double meanY = stepsY.Average();
                    double sumSqY = stepsY.Sum(y => Math.Pow(y - meanY, 2));
                    double stdDevY = Math.Sqrt(sumSqY / stepsY.Count);

                    // Đường thẳng tuyệt đối trục Y không rung lắc -> Bot kéo tự động
                    if (stdDevY < 0.05)
                    {
                        penalties += 0.35;
                        result.Reasons.Add("Perfect straight line mouse movement detected.");
                    }
                }
            }

            // 3. Phân tích hành vi gõ phím (Keystroke Dynamics)
            var keyActions = telemetry.KeyActions;
            if (keyActions != null && keyActions.Count > 0)
            {
                var sortedKeys = keyActions.OrderBy(k => k.T).ToList();
                var keyIntervals = new List<long>();
                
                for (int i = 1; i < sortedKeys.Count; i++)
                {
                    long dt = sortedKeys[i].T - sortedKeys[i - 1].T;
                    if (dt >= 0)
                    {
                        keyIntervals.Add(dt);
                    }
                }

                if (keyIntervals.Count > 0)
                {
                    double avgInterval = keyIntervals.Average();
                    // Tốc độ gõ phím nhanh bất thường (ví dụ: trung bình dưới 10ms mỗi phím -> dán text bằng bot)
                    if (avgInterval < 12.0)
                    {
                        penalties += 0.3;
                        result.Reasons.Add("Instant keystrokes detected (pasted or programmatic typing).");
                    }
                }
            }

            // 4. Phân tích vân tay trình duyệt không hợp lệ
            if (fp.ScreenWidth <= 0 || fp.ScreenHeight <= 0)
            {
                penalties += 0.4;
                result.Reasons.Add("Invalid display screen geometry.");
            }

            // Tính điểm số cuối cùng
            result.Score = Math.Max(0.0, 1.0 - penalties);
            
            // Nếu điểm số dưới 0.7 thì gắn nhãn là Bot và yêu cầu Fallback
            if (result.Score < 0.7)
            {
                result.IsBot = true;
            }

            return result;
        }
    }
}
