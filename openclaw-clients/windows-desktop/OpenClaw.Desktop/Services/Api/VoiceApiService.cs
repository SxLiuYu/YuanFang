using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using OpenClaw.Desktop.Models;

namespace OpenClaw.Desktop.Services.Api
{
    public class VoiceApiService
    {
        private readonly ApiClient _apiClient;
        private readonly string _baseUrl = "http://localhost:8082/api/v1/voice";

        public VoiceApiService(ApiClient apiClient)
        {
            _apiClient = apiClient;
        }

        public async Task<VoiceCommandResponse> ExecuteDeviceControlAsync(string text, Dictionary<string, object>? context = null)
        {
            var request = new VoiceCommandRequest
            {
                Text = text,
                Context = context
            };

            var response = await _apiClient.PostAsync<VoiceCommandResponse>(
                $"{_baseUrl}/control/device",
                request
            );

            return response ?? new VoiceCommandResponse { Success = false, Message = "请求失败" };
        }

        public async Task<VoiceCommandResponse> ExecuteSceneControlAsync(string text, Dictionary<string, object>? context = null)
        {
            var request = new VoiceCommandRequest
            {
                Text = text,
                Context = context
            };

            var response = await _apiClient.PostAsync<VoiceCommandResponse>(
                $"{_baseUrl}/control/scene",
                request
            );

            return response ?? new VoiceCommandResponse { Success = false, Message = "请求失败" };
        }

        public async Task<List<VoiceSuggestion>> GetSuggestionsAsync(string? userId = null)
        {
            var url = $"{_baseUrl}/suggestions";
            if (!string.IsNullOrEmpty(userId))
            {
                url += $"?user_id={Uri.EscapeDataString(userId)}";
            }

            var response = await _apiClient.GetAsync<List<VoiceSuggestion>>(url);
            return response ?? new List<VoiceSuggestion>();
        }

        public async Task<ScheduleParseResponse> ParseScheduleAsync(string text, string? userId = null)
        {
            var request = new ScheduleParseRequest
            {
                Text = text,
                UserId = userId
            };

            var response = await _apiClient.PostAsync<ScheduleParseResponse>(
                $"{_baseUrl}/schedule/parse",
                request
            );

            return response ?? new ScheduleParseResponse { Success = false };
        }

        public async Task<VoiceCommandResponse> ProcessCommandAsync(string text, Dictionary<string, object>? context = null)
        {
            var request = new VoiceCommandRequest
            {
                Text = text,
                Context = context
            };

            var response = await _apiClient.PostAsync<VoiceCommandResponse>(
                $"{_baseUrl}/command",
                request
            );

            return response ?? new VoiceCommandResponse { Success = false, Message = "请求失败" };
        }
    }
}