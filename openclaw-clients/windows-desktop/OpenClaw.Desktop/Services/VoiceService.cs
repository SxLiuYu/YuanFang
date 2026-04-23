using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace OpenClaw.Desktop.Services
{
    public class VoiceService : IDisposable
    {
        private readonly Dictionary<string, VoiceCommand> _commands;
        private bool _disposed;
        private bool _isListening;

        public event EventHandler<SpeechRecognizedEventArgs>? CommandRecognized;
        public event EventHandler<SpeechRecognizedEventArgs>? SpeechRecognized;
        public event EventHandler<VoiceErrorEventArgs>? ErrorOccurred;
        public event EventHandler? ListeningStarted;
        public event EventHandler? ListeningStopped;

        public bool IsListening => _isListening;
        public IReadOnlyDictionary<string, VoiceCommand> Commands => _commands;

        public VoiceService()
        {
            _commands = new Dictionary<string, VoiceCommand>(StringComparer.OrdinalIgnoreCase);
        }

        public void RegisterCommand(VoiceCommand command)
        {
            if (command == null || string.IsNullOrWhiteSpace(command.CommandText))
                return;

            _commands[command.CommandText] = command;
        }

        public void UnregisterCommand(string commandText)
        {
            _commands.Remove(commandText);
        }

        public void ClearCommands()
        {
            _commands.Clear();
        }

        public async Task StartListeningAsync()
        {
            _isListening = true;
            ListeningStarted?.Invoke(this, EventArgs.Empty);
            await Task.CompletedTask;
        }

        public async Task StopListeningAsync()
        {
            _isListening = false;
            ListeningStopped?.Invoke(this, EventArgs.Empty);
            await Task.CompletedTask;
        }

        public async Task SpeakAsync(string text)
        {
            System.Diagnostics.Debug.WriteLine($"[TTS] {text}");
            await Task.CompletedTask;
        }

        public List<string> GetAvailableVoices()
        {
            return new List<string> { "Default" };
        }

        public void SetVoice(string voiceName)
        {
        }

        public void SetVolume(int volume)
        {
        }

        public void SetRate(int rate)
        {
        }

        public void Dispose()
        {
            if (_disposed) return;
            _disposed = true;
            GC.SuppressFinalize(this);
        }
    }

    public class VoiceCommand
    {
        public string CommandText { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public Action? Action { get; set; }
        public List<string> Aliases { get; set; } = new();
    }

    public class SpeechRecognizedEventArgs : EventArgs
    {
        public string Text { get; set; } = string.Empty;
        public float Confidence { get; set; }
    }

    public class VoiceErrorEventArgs : EventArgs
    {
        public string Operation { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public Exception? Exception { get; set; }
    }
}