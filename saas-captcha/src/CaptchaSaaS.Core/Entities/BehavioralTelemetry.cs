using System;
using System.Collections.Generic;

namespace CaptchaSaaS.Core.Entities
{
    public class BehavioralTelemetry
    {
        public List<MousePoint> MouseActions { get; set; } = new List<MousePoint>();
        public List<KeyAction> KeyActions { get; set; } = new List<KeyAction>();
        public List<ClickAction> ClickActions { get; set; } = new List<ClickAction>();
        public List<ScrollAction> ScrollActions { get; set; } = new List<ScrollAction>();
        public BrowserFingerprint Fingerprint { get; set; } = new BrowserFingerprint();
    }

    public class MousePoint
    {
        public double X { get; set; }
        public double Y { get; set; }
        public long T { get; set; } // Timestamp in ms
    }

    public class KeyAction
    {
        public string Key { get; set; } = string.Empty;
        public string Type { get; set; } = string.Empty; // "keydown" or "keyup"
        public long T { get; set; } // Timestamp in ms
    }

    public class ClickAction
    {
        public double X { get; set; }
        public double Y { get; set; }
        public string Target { get; set; } = string.Empty; // Target element identifier
        public long T { get; set; } // Timestamp in ms
    }

    public class ScrollAction
    {
        public double ScrollTop { get; set; }
        public long T { get; set; } // Timestamp in ms
    }

    public class BrowserFingerprint
    {
        public string UserAgent { get; set; } = string.Empty;
        public int ScreenWidth { get; set; }
        public int ScreenHeight { get; set; }
        public bool Webdriver { get; set; } // navigator.webdriver flag
        public string CanvasHash { get; set; } = string.Empty; // WebGL/Canvas Fingerprint
        public int TimezoneOffset { get; set; }
        public string Languages { get; set; } = string.Empty;
        public bool IsHeadless { get; set; } // client-side self-check
    }
}
