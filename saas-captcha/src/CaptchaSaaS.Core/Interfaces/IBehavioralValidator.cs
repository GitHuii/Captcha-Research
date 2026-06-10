using System.Collections.Generic;
using CaptchaSaaS.Core.Entities;

namespace CaptchaSaaS.Core.Interfaces
{
    public class BehavioralEvaluationResult
    {
        public double Score { get; set; } // 0.0 to 1.0 (1.0 is most likely human)
        public bool IsBot { get; set; }
        public List<string> Reasons { get; set; } = new List<string>();
    }

    public interface IBehavioralValidator
    {
        BehavioralEvaluationResult Evaluate(BehavioralTelemetry telemetry);
    }
}
