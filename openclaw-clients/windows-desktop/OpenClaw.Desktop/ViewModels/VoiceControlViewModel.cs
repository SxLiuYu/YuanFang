using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using OpenClaw.Desktop.Models;
using OpenClaw.Desktop.Services.Api;
using OpenClaw.Desktop.Services.Voice;

namespace OpenClaw.Desktop.ViewModels
{
    public partial class VoiceControlViewModel : BaseViewModel
    {
        private readonly VoiceApiService _voiceApiService;
        private readonly VoiceRecognitionService _voiceRecognitionService;
        private readonly TTSService _ttsService;

        [ObservableProperty]
        private bool _isListening;

        [ObservableProperty]
        private string _recognizedText = "按下麦克风开始说话...";

        [ObservableProperty]
        private string _responseMessage = "";

        [ObservableProperty]
        private bool _isProcessing;

        [ObservableProperty]
        private double _audioLevel;

        public ObservableCollection<VoiceSuggestion> Suggestions { get; } = new();

        public ICommand ToggleListeningCommand { get; }
        public ICommand ExecuteSuggestionCommand { get; }
        public ICommand ClearCommand { get; }

        public VoiceControlViewModel(
            VoiceApiService voiceApiService,
            VoiceRecognitionService voiceRecognitionService,
            TTSService ttsService)
        {
            _voiceApiService = voiceApiService;
            _voiceRecognitionService = voiceRecognitionService;
            _ttsService = ttsService;

            ToggleListeningCommand = new AsyncRelayCommand(ToggleListeningAsync);
            ExecuteSuggestionCommand = new AsyncRelayCommand<VoiceSuggestion>(ExecuteSuggestionAsync);
            ClearCommand = new RelayCommand(Clear);

            _voiceRecognitionService.AudioLevelChanged += (s, level) => AudioLevel = level;
            _voiceRecognitionService.Recognized += OnVoiceRecognized;
        }

        private async Task ToggleListeningAsync()
        {
            if (IsListening)
            {
                await StopListeningAsync();
            }
            else
            {
                await StartListeningAsync();
            }
        }

        private async Task StartListeningAsync()
        {
            IsListening = true;
            RecognizedText = "正在听...";
            
            await _voiceRecognitionService.StartListeningAsync();
        }

        private async Task StopListeningAsync()
        {
            IsListening = false;
            await _voiceRecognitionService.StopListeningAsync();
        }

        private async void OnVoiceRecognized(object? sender, string text)
        {
            RecognizedText = text;
            await ProcessCommandAsync(text);
        }

        private async Task ProcessCommandAsync(string text)
        {
            if (string.IsNullOrWhiteSpace(text))
                return;

            IsProcessing = true;
            ResponseMessage = "正在处理...";

            try
            {
                var response = await _voiceApiService.ProcessCommandAsync(text);

                if (response.Success)
                {
                    ResponseMessage = response.Message;

                    Suggestions.Clear();
                    foreach (var suggestion in response.Suggestions)
                    {
                        Suggestions.Add(suggestion);
                    }

                    await _ttsService.SpeakAsync(response.Message);
                }
                else
                {
                    ResponseMessage = response.Message;
                }
            }
            catch (Exception ex)
            {
                ResponseMessage = $"处理失败: {ex.Message}";
            }
            finally
            {
                IsProcessing = false;
            }
        }

        private async Task ExecuteSuggestionAsync(VoiceSuggestion? suggestion)
        {
            if (suggestion == null)
                return;

            IsProcessing = true;
            ResponseMessage = $"正在执行: {suggestion.Title}";

            try
            {
                var action = suggestion.Action;
                var actionType = action.GetValueOrDefault("type")?.ToString();

                if (actionType == "device_control")
                {
                    var device = action.GetValueOrDefault("device")?.ToString() ?? "";
                    var deviceAction = action.GetValueOrDefault("action")?.ToString() ?? "";
                    
                    var command = $"{deviceAction} {device}".Trim();
                    var response = await _voiceApiService.ExecuteDeviceControlAsync(command);
                    
                    ResponseMessage = response.Message;
                    await _ttsService.SpeakAsync(response.Message);
                }
                else if (actionType == "scene")
                {
                    var scene = action.GetValueOrDefault("scene")?.ToString() ?? "";
                    var response = await _voiceApiService.ExecuteSceneControlAsync(scene);
                    
                    ResponseMessage = response.Message;
                    await _ttsService.SpeakAsync(response.Message);
                }
            }
            catch (Exception ex)
            {
                ResponseMessage = $"执行失败: {ex.Message}";
            }
            finally
            {
                IsProcessing = false;
            }
        }

        private void Clear()
        {
            RecognizedText = "按下麦克风开始说话...";
            ResponseMessage = "";
            Suggestions.Clear();
        }

        public async Task LoadSuggestionsAsync()
        {
            try
            {
                var suggestions = await _voiceApiService.GetSuggestionsAsync();
                
                Suggestions.Clear();
                foreach (var suggestion in suggestions)
                {
                    Suggestions.Add(suggestion);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"加载建议失败: {ex.Message}");
            }
        }
    }
}