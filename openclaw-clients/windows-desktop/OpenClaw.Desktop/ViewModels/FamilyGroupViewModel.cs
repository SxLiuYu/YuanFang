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
    public partial class FamilyGroupViewModel : BaseViewModel
    {
        private readonly FamilyApiService _familyApiService;

        [ObservableProperty]
        private string _currentUserId = "user_default";

        [ObservableProperty]
        private string _newGroupName = "";

        [ObservableProperty]
        private string _inviteCode = "";

        [ObservableProperty]
        private FamilyGroup? _selectedGroup;

        [ObservableProperty]
        private bool _isLoading;

        public ObservableCollection<UserGroupInfo> MyGroups { get; } = new();
        public ObservableCollection<FamilyMember> Members { get; } = new();
        public ObservableCollection<SharedSchedule> Schedules { get; } = new();
        public ObservableCollection<MemberLocation> MemberLocations { get; } = new();

        public ICommand CreateGroupCommand { get; }
        public ICommand JoinGroupCommand { get; }
        public ICommand LoadGroupsCommand { get; }
        public ICommand SelectGroupCommand { get; }
        public ICommand ShareLocationCommand { get; }
        public ICommand CreateScheduleCommand { get; }

        public FamilyGroupViewModel(FamilyApiService familyApiService)
        {
            _familyApiService = familyApiService;

            CreateGroupCommand = new AsyncRelayCommand(CreateGroupAsync, () => !string.IsNullOrWhiteSpace(NewGroupName));
            JoinGroupCommand = new AsyncRelayCommand(JoinGroupAsync, () => !string.IsNullOrWhiteSpace(InviteCode));
            LoadGroupsCommand = new AsyncRelayCommand(LoadGroupsAsync);
            SelectGroupCommand = new AsyncRelayCommand<UserGroupInfo>(SelectGroupAsync);
            ShareLocationCommand = new AsyncRelayCommand(ShareLocationAsync);
            CreateScheduleCommand = new AsyncRelayCommand(CreateScheduleAsync);
        }

        private async Task LoadGroupsAsync()
        {
            IsLoading = true;

            try
            {
                var groups = await _familyApiService.GetUserGroupsAsync(CurrentUserId);

                MyGroups.Clear();
                foreach (var group in groups)
                {
                    MyGroups.Add(group);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"加载群组失败: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }

        private async Task CreateGroupAsync()
        {
            if (string.IsNullOrWhiteSpace(NewGroupName))
                return;

            IsLoading = true;

            try
            {
                var result = await _familyApiService.CreateGroupAsync(NewGroupName, CurrentUserId);

                if (result.TryGetValue("success", out var success) && success is bool isSuccess && isSuccess)
                {
                    NewGroupName = "";
                    await LoadGroupsAsync();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"创建群组失败: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }

        private async Task JoinGroupAsync()
        {
            if (string.IsNullOrWhiteSpace(InviteCode))
                return;

            IsLoading = true;

            try
            {
                var result = await _familyApiService.JoinGroupAsync(InviteCode, CurrentUserId, CurrentUserId);

                if (result.TryGetValue("success", out var success) && success is bool isSuccess && isSuccess)
                {
                    InviteCode = "";
                    await LoadGroupsAsync();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"加入群组失败: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }

        private async Task SelectGroupAsync(UserGroupInfo? groupInfo)
        {
            if (groupInfo == null)
                return;

            IsLoading = true;

            try
            {
                SelectedGroup = await _familyApiService.GetGroupAsync(groupInfo.Id);

                if (SelectedGroup != null)
                {
                    Members.Clear();
                    foreach (var member in SelectedGroup.Members)
                    {
                        Members.Add(member);
                    }

                    var locations = await _familyApiService.GetMemberLocationsAsync(groupInfo.Id);
                    MemberLocations.Clear();
                    foreach (var location in locations)
                    {
                        MemberLocations.Add(location);
                    }

                    var schedules = await _familyApiService.GetSharedSchedulesAsync(groupInfo.Id);
                    Schedules.Clear();
                    foreach (var schedule in schedules)
                    {
                        Schedules.Add(schedule);
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"加载群组详情失败: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }

        private async Task ShareLocationAsync()
        {
            if (SelectedGroup == null)
                return;

            try
            {
                var request = new LocationShareRequest
                {
                    UserId = CurrentUserId,
                    Latitude = 39.9042,
                    Longitude = 116.4074,
                    Address = "北京市东城区"
                };

                await _familyApiService.ShareLocationAsync(SelectedGroup.Id, request);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"分享位置失败: {ex.Message}");
            }
        }

        private async Task CreateScheduleAsync()
        {
            if (SelectedGroup == null)
                return;

            try
            {
                var request = new SharedScheduleCreate
                {
                    GroupId = SelectedGroup.Id,
                    Title = "家庭会议",
                    StartTime = DateTime.Now.AddDays(1),
                    EndTime = DateTime.Now.AddDays(1).AddHours(1)
                };

                var result = await _familyApiService.CreateSharedScheduleAsync(request);

                if (result.TryGetValue("success", out var success) && success is bool isSuccess && isSuccess)
                {
                    await SelectGroupAsync(new UserGroupInfo { Id = SelectedGroup.Id });
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"创建日程失败: {ex.Message}");
            }
        }

        public async Task InitializeAsync()
        {
            await LoadGroupsAsync();
        }
    }
}