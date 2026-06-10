using System.Collections.Generic;

namespace CaptchaSaaS.Core.Interfaces
{
    public interface ISliderTrajectoryValidator
    {
        bool Validate(List<TrajectoryPointV2> trajectory, out string reason);
    }

    public class TrajectoryPointV2
    {
        public double X { get; set; }
        public double Y { get; set; }
        public long T { get; set; } // timestamp in milliseconds
    }
}
