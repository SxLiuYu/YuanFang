using System;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace OpenClaw.Desktop.Services.Voice
{
    public class VoiceRecognitionService : IDisposable
    {
        private bool _isListening;
        private bool _disposed;

        public event EventHandler<double>? AudioLevelChanged;
        public event EventHandler<string>? Recognized;
        public event EventHandler<string>? Error;

        public bool IsListening => _isListening;

        public VoiceRecognitionService()
        {
        }

        public Task StartListeningAsync()
        {
            _isListening = true;
            Error?.Invoke(this, "语音识别需要安装Windows SDK，当前版本暂不支持");
            return Task.CompletedTask;
        }

        public Task StopListeningAsync()
        {
            _isListening = false;
            return Task.CompletedTask;
        }

        public void Dispose()
        {
            if (_disposed)
                return;
            _disposed = true;
        }
    }

    public class TTSService : IDisposable
    {
        private bool _disposed;

        public event EventHandler<string>? Error;

        public TTSService()
        {
        }

        public Task SpeakAsync(string text)
        {
            Error?.Invoke(this, "语音合成需要安装Windows SDK，当前版本暂不支持");
            return Task.CompletedTask;
        }

        public Task SetVoiceAsync(string voiceName)
        {
            return Task.CompletedTask;
        }

        public Task<List<string>> GetAvailableVoicesAsync()
        {
            return Task.FromResult(new List<string>());
        }

        public void Dispose()
        {
            if (_disposed)
                return;
            _disposed = true;
        }
    }
}
