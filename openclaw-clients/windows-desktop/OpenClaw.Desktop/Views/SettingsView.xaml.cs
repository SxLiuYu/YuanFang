using System.Windows;
using System.Windows.Controls;
using OpenClaw.Desktop.ViewModels;

namespace OpenClaw.Desktop.Views;

public partial class SettingsView : UserControl
{
    public SettingsView()
    {
        InitializeComponent();
    }

    private void ApiTokenBox_PasswordChanged(object sender, RoutedEventArgs e)
    {
        if (DataContext is SettingsViewModel viewModel && sender is PasswordBox passwordBox)
        {
            viewModel.ApiToken = passwordBox.Password;
        }
    }
}