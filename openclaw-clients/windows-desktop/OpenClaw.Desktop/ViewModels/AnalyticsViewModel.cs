using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using OpenClaw.Desktop.Models;
using OpenClaw.Desktop.Services.Api;

namespace OpenClaw.Desktop.ViewModels
{
    public partial class AnalyticsViewModel : BaseViewModel
    {
        private readonly AnalyticsApiService _analyticsApiService;

        [ObservableProperty]
        private string _currentUserId = "user_default";

        [ObservableProperty]
        private bool _isLoading;

        [ObservableProperty]
        private double _healthScore;

        [ObservableProperty]
        private string _healthGrade = "--";

        [ObservableProperty]
        private HealthComponents? _healthComponents;

        [ObservableProperty]
        private FinanceInsightResponse? _financeInsight;

        [ObservableProperty]
        private ReportResponse? _currentReport;

        public ObservableCollection<string> Suggestions { get; } = new();
        public ObservableCollection<CategoryExpense> Categories { get; } = new();
        public ObservableCollection<AnomalyResponse> Anomalies { get; } = new();

        public ICommand RefreshHealthCommand { get; }
        public ICommand RefreshFinanceCommand { get; }
        public ICommand CheckAnomaliesCommand { get; }
        public ICommand GenerateWeeklyReportCommand { get; }
        public ICommand GenerateMonthlyReportCommand { get; }

        public AnalyticsViewModel(AnalyticsApiService analyticsApiService)
        {
            _analyticsApiService = analyticsApiService;

            RefreshHealthCommand = new AsyncRelayCommand(RefreshHealthAsync);
            RefreshFinanceCommand = new AsyncRelayCommand(RefreshFinanceAsync);
            CheckAnomaliesCommand = new AsyncRelayCommand(CheckAnomaliesAsync);
            GenerateWeeklyReportCommand = new AsyncRelayCommand(GenerateWeeklyReportAsync);
            GenerateMonthlyReportCommand = new AsyncRelayCommand(GenerateMonthlyReportAsync);
        }

        private async Task RefreshHealthAsync()
        {
            IsLoading = true;

            try
            {
                var result = await _analyticsApiService.GetHealthScoreAsync(CurrentUserId);

                if (result != null && result.Success)
                {
                    HealthScore = result.Score;
                    HealthGrade = result.Grade;
                    HealthComponents = result.Components;

                    Suggestions.Clear();
                    foreach (var suggestion in result.Suggestions)
                    {
                        Suggestions.Add(suggestion);
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"获取健康评分失败: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }

        private async Task RefreshFinanceAsync()
        {
            IsLoading = true;

            try
            {
                var result = await _analyticsApiService.GetFinanceInsightsAsync(CurrentUserId);

                if (result != null && result.Success)
                {
                    FinanceInsight = result;

                    Categories.Clear();
                    foreach (var category in result.Categories)
                    {
                        Categories.Add(category);
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"获取消费洞察失败: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }

        private async Task CheckAnomaliesAsync()
        {
            try
            {
                var healthAnomalies = await _analyticsApiService.CheckAnomaliesAsync(CurrentUserId, "health");
                var financeAnomalies = await _analyticsApiService.CheckAnomaliesAsync(CurrentUserId, "finance");

                Anomalies.Clear();
                foreach (var anomaly in healthAnomalies)
                {
                    Anomalies.Add(anomaly);
                }
                foreach (var anomaly in financeAnomalies)
                {
                    Anomalies.Add(anomaly);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"检测异常失败: {ex.Message}");
            }
        }

        private async Task GenerateWeeklyReportAsync()
        {
            IsLoading = true;

            try
            {
                CurrentReport = await _analyticsApiService.GenerateWeeklyReportAsync(CurrentUserId);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"生成周报失败: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }

        private async Task GenerateMonthlyReportAsync()
        {
            IsLoading = true;

            try
            {
                CurrentReport = await _analyticsApiService.GenerateMonthlyReportAsync(CurrentUserId);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"生成月报失败: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }

        public async Task InitializeAsync()
        {
            await RefreshHealthAsync();
            await RefreshFinanceAsync();
            await CheckAnomaliesAsync();
        }
    }
}