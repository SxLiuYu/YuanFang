using System;
using System.IO;
using Newtonsoft.Json;
using OpenClaw.Desktop.Models;

namespace OpenClaw.Desktop.Services
{
    public class ConfigService
    {
        private readonly string _configPath;
        private readonly string _configDir;
        
        public AppConfig Config { get; private set; }
        
        public event EventHandler? ConfigChanged;
        
        public ConfigService()
        {
            _configDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "OpenClaw");
            _configPath = Path.Combine(_configDir, "config.json");
            
            Config = Load();
        }
        
        public AppConfig Load()
        {
            try
            {
                if (File.Exists(_configPath))
                {
                    var json = File.ReadAllText(_configPath);
                    var config = JsonConvert.DeserializeObject<AppConfig>(json);
                    if (config != null)
                    {
                        System.Diagnostics.Debug.WriteLine($"配置已加载: {_configPath}");
                        return config;
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"加载配置失败: {ex.Message}");
            }
            
            return new AppConfig();
        }
        
        public void Save()
        {
            try
            {
                if (!Directory.Exists(_configDir))
                {
                    Directory.CreateDirectory(_configDir);
                }
                
                var json = JsonConvert.SerializeObject(Config, Formatting.Indented);
                File.WriteAllText(_configPath, json);
                
                System.Diagnostics.Debug.WriteLine($"配置已保存: {_configPath}");
                ConfigChanged?.Invoke(this, EventArgs.Empty);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"保存配置失败: {ex.Message}");
            }
        }
        
        public void Reset()
        {
            Config = new AppConfig();
            Save();
        }
        
        public void UpdateTheme(string theme)
        {
            Config.Theme = theme;
            Save();
        }
        
        public void UpdateServerUrl(string url)
        {
            Config.ServerUrl = url;
            Save();
        }
        
        public void UpdateApiToken(string token)
        {
            Config.ApiToken = token;
            Save();
        }
        
        public void UpdateUserName(string name)
        {
            Config.UserName = name;
            Save();
        }
        
        public T? Get<T>(string key, T? defaultValue = default)
        {
            var prop = typeof(AppConfig).GetProperty(key);
            if (prop != null)
            {
                var value = prop.GetValue(Config);
                if (value is T typedValue)
                    return typedValue;
            }
            return defaultValue;
        }
        
        public void Set<T>(string key, T value)
        {
            var prop = typeof(AppConfig).GetProperty(key);
            if (prop != null && prop.CanWrite)
            {
                prop.SetValue(Config, value);
                Save();
            }
        }
    }
}