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

public class FinanceViewModel : BaseViewModel
{
    private readonly ApiClient _apiClient;

    public ObservableCollection<FinanceRecord> Records { get; }

    private FinanceSummary? _summary;
    public FinanceSummary? Summary
    {
        get => _summary;
        set => SetProperty(ref _summary, value);
    }

    private decimal _monthlyBudget = 10000;
    public decimal MonthlyBudget
    {
        get => _monthlyBudget;
        set => SetProperty(ref _monthlyBudget, value);
    }

    public ISeries[] ExpenseSeries { get; private set; } = Array.Empty<ISeries>();
    public ISeries[] IncomeExpenseSeries { get; private set; } = Array.Empty<ISeries>();

    public ICommand RefreshCommand { get; }
    public ICommand AddIncomeCommand { get; }
    public ICommand AddExpenseCommand { get; }

    public FinanceViewModel() : this(null!) { }

    public FinanceViewModel(ApiClient apiClient)
    {
        _apiClient = apiClient;
        Records = new ObservableCollection<FinanceRecord>();

        RefreshCommand = new RelayCommand(async () => await LoadDataAsync());
        AddIncomeCommand = new RelayCommand(() => AddRecord("Income"));
        AddExpenseCommand = new RelayCommand(() => AddRecord("Expense"));

        _ = LoadDataAsync();
    }

    private async Task LoadDataAsync()
    {
        IsLoading = true;
        StatusMessage = "Loading finance data...";

        try
        {
            var data = await _apiClient.GetFinanceRecordsAsync(
                new DateTime(DateTime.Today.Year, DateTime.Today.Month, 1),
                DateTime.Today);

            Records.Clear();
            foreach (var record in data)
            {
                Records.Add(record);
            }

            UpdateCharts();
            await LoadSummaryAsync();
            StatusMessage = $"Loaded {Records.Count} records";
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
        Summary = await _apiClient.GetFinanceSummaryAsync(
            new DateTime(DateTime.Today.Year, DateTime.Today.Month, 1),
            DateTime.Today);
    }

    private void UpdateCharts()
    {
        var categories = Records
            .Where(r => r.Type == "Expense")
            .GroupBy(r => r.Category)
            .Select(g => new { Category = g.Key, Total = g.Sum(r => r.Amount) })
            .OrderByDescending(x => x.Total)
            .Take(6)
            .ToList();

        ExpenseSeries = new ISeries[]
        {
            new PieSeries<decimal>
            {
                Values = categories.Select(c => c.Total).ToArray(),
                Name = "Expenses",
                DataLabelsPaint = new SolidColorPaint(SKColor.Parse("#FFFFFF"))
            }
        };

        var dailyExpense = Records
            .Where(r => r.Type == "Expense")
            .GroupBy(r => r.Date.Date)
            .Select(g => new { Date = g.Key, Total = g.Sum(r => r.Amount) })
            .OrderBy(x => x.Date)
            .ToList();

        var dailyIncome = Records
            .Where(r => r.Type == "Income")
            .GroupBy(r => r.Date.Date)
            .Select(g => new { Date = g.Key, Total = g.Sum(r => r.Amount) })
            .OrderBy(x => x.Date)
            .ToList();

        IncomeExpenseSeries = new ISeries[]
        {
            new ColumnSeries<decimal>
            {
                Values = dailyExpense.Select(d => d.Total).ToArray(),
                Name = "Expense",
                Fill = new SolidColorPaint(SKColor.Parse("#EF5350"))
            },
            new ColumnSeries<decimal>
            {
                Values = dailyIncome.Select(d => d.Total).ToArray(),
                Name = "Income",
                Fill = new SolidColorPaint(SKColor.Parse("#66BB6A"))
            }
        };

        OnPropertyChanged(nameof(ExpenseSeries));
        OnPropertyChanged(nameof(IncomeExpenseSeries));
    }

    private void AddRecord(string type)
    {
        var record = new FinanceRecord
        {
            Date = DateTime.Today,
            Type = type,
            Category = type == "Income" ? "Salary" : "Food",
            Amount = 0,
            CreatedAt = DateTime.Now,
            UpdatedAt = DateTime.Now
        };
        Records.Insert(0, record);
        StatusMessage = $"New {type.ToLower()} record added";
    }
}