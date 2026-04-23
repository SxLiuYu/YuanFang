using System;
using System.IO;
using Newtonsoft.Json;

namespace OpenClaw.Desktop.Models
{
    public class AppConfig
    {
        public bool LaunchAtStartup { get; set; } = true;
        public bool MinimizeToTray { get; set; } = true;
        public bool ShowNotifications { get; set; } = true;
        public string ServerUrl { get; set; } = "http://localhost:8000";
        public string ApiToken { get; set; } = "";
        public string Theme { get; set; } = "Light";
        public string UserName { get; set; } = "用户";
        public WindowConfig? Window { get; set; }
    }

    public class WindowConfig
    {
        public double Left { get; set; }
        public double Top { get; set; }
        public double Width { get; set; } = 1000;
        public double Height { get; set; } = 700;
        public bool IsMaximized { get; set; }
    }
}