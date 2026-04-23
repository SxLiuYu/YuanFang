using System.Collections.Generic;
using System.Threading.Tasks;
using OpenClaw.Desktop.Models;

namespace OpenClaw.Desktop.Services.Api
{
    public class AnalyticsApiService
    {
        private readonly ApiClient _apiClient;
        private readonly string _baseUrl = "http://localhost:8082/api/v1/analytics";

        public AnalyticsApiService(ApiClient apiClient)
        {
            _apiClient = apiClient;
        }

        public async Task<HealthScoreResponse?> GetHealthScoreAsync(string userId, string? deviceId = null)
        {
            var url = $"{_baseUrl}/health/score?user_id={userId}";
            if (!string.IsNullOrEmpty(deviceId))
                url += $"&device_id={deviceId}";
            
            return await _apiClient.GetAsync<HealthScoreResponse>(url);
        }

        public async Task<FinanceInsightResponse?> GetFinanceInsightsAsync(string userId, int periodDays = 30)
        {
            return await _apiClient.GetAsync<FinanceInsightResponse>(
                $"{_baseUrl}/finance/insights?user_id={userId}&period_days={periodDays}"
            );
        }

        public async Task<List<AnomalyResponse>> CheckAnomaliesAsync(string userId, string dataType)
        {
            var result = await _apiClient.GetAsync<List<AnomalyResponse>>(
                $"{_baseUrl}/anomalies?user_id={userId}&data_type={dataType}"
            );
            return result ?? new List<AnomalyResponse>();
        }

        public async Task<ReportResponse?> GenerateWeeklyReportAsync(string userId)
        {
            return await _apiClient.GetAsync<ReportResponse>(
                $"{_baseUrl}/report/weekly?user_id={userId}"
            );
        }

        public async Task<ReportResponse?> GenerateMonthlyReportAsync(string userId)
        {
            return await _apiClient.GetAsync<ReportResponse>(
                $"{_baseUrl}/report/monthly?user_id={userId}"
            );
        }
    }
}