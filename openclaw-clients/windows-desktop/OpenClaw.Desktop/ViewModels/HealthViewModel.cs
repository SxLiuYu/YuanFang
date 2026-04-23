using System.Collections.ObjectModel;
using System.Windows.Input;
using CommunityToolkit.Mvvm.Input;
using LiveChartsCore;
using LiveChartsCore.SkiaSharpView;
using LiveChartsCore.SkiaSharpView.Painting;
using SkiaSharp;
using OpenClaw.Desktop.Models;
using OpenClaw.Desktop.Services;

namespace OpenClaw.Desktop.ViewModels;

public class HealthViewModel : BaseViewModel
{
    private readonly ApiClient _apiClient;

    public ObservableCollection<HealthData> HealthRecords { get; }

    private HealthSummary? _summary;
    public HealthSummary? Summary
    {
        get => _summary;
        set => SetProperty(ref _summary, value);
    }

    public ISeries[] StepSeries { get; private set; } = Array.Empty<ISeries>();
    public Axis[] XAxes { get; } = { new Axis() };
    public Axis[] YAxes { get; } = { new Axis() };

    public ICommand RefreshCommand { get; }
    public ICommand AddRecordCommand { get; }

    public HealthViewModel() : this(null!) { }

    public HealthViewModel(ApiClient apiClient)
    {
        _apiClient = apiClient;
        HealthRecords = new ObservableCollection<HealthData>();

        RefreshCommand = new RelayCommand(async () => await LoadDataAsync());
        AddRecordCommand = new RelayCommand(AddNewRecord);

        _ = LoadDataAsync();
    }

    private async Task LoadDataAsync()
    {
        IsLoading = true;
        StatusMessage = "Loading health data...";

        try
        {
            var data = await _apiClient.GetHealthDataAsync(DateTime.Today.AddDays(-7), DateTime.Today);
            
            HealthRecords.Clear();
            foreach (var record in data)
            {
                HealthRecords.Add(record);
            }

            UpdateChart();
            await LoadSummaryAsync();
            StatusMessage = $"Loaded {HealthRecords.Count} records";
        }
        catch (Exception ex)
        {
            StatusMessage = $"Error: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }

    private async Task LoadSummaryAsync()
    {
        Summary = await _apiClient.GetHealthSummaryAsync(DateTime.Today.AddDays(-30), DateTime.Today);
    }

    private void UpdateChart()
    {
        StepSeries = new ISeries[]
        {
            new LineSeries<double>
            {
                Values = HealthRecords.Select(r => (double)r.Steps).ToArray(),
                Fill = new LinearGradientPaint(new[]
                {
                    new SKColor(126, 87, 194),
                    new SKColor(126, 87, 194, 0)
                }),
                Stroke = new SolidColorPaint(SKColor.Parse("#7E57C2")),
                GeometryStroke = new SolidColorPaint(SKColor.Parse("#7E57C2")),
                GeometryFill = new SolidColorPaint(SKColor.Parse("#FFFFFF"))
            }
        };

        XAxes[0].Labels = HealthRecords.Select(r => r.Date.ToString("MM/dd")).ToArray();
        OnPropertyChanged(nameof(StepSeries));
    }

    private void AddNewRecord()
    {
        var newRecord = new HealthData
        {
            Date = DateTime.Today,
            Steps = 0,
            Distance = 0,
            Calories = 0,
            HeartRate = 70,
            SleepHours = 8,
            Weight = 70,
            CreatedAt = DateTime.Now,
            UpdatedAt = DateTime.Now
        };
        HealthRecords.Insert(0, newRecord);
        StatusMessage = "New record added. Edit and save.";
    }
}