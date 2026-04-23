using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using OpenClaw.Desktop.Models;

namespace OpenClaw.Desktop.Services.Api
{
    public class FamilyApiService
    {
        private readonly ApiClient _apiClient;
        private readonly string _baseUrl = "http://localhost:8082/api/v1/family";

        public FamilyApiService(ApiClient apiClient)
        {
            _apiClient = apiClient;
        }

        public async Task<Dictionary<string, object>> CreateGroupAsync(string name, string ownerId)
        {
            var request = new FamilyGroupCreate
            {
                Name = name,
                OwnerId = ownerId
            };

            return await _apiClient.PostAsync<Dictionary<string, object>>(
                $"{_baseUrl}/groups",
                request
            ) ?? new Dictionary<string, object>();
        }

        public async Task<FamilyGroup?> GetGroupAsync(string groupId)
        {
            return await _apiClient.GetAsync<FamilyGroup>($"{_baseUrl}/groups/{groupId}");
        }

        public async Task<List<UserGroupInfo>> GetUserGroupsAsync(string userId)
        {
            var result = await _apiClient.GetAsync<List<UserGroupInfo>>($"{_baseUrl}/user/{userId}/groups");
            return result ?? new List<UserGroupInfo>();
        }

        public async Task<Dictionary<string, object>> JoinGroupAsync(string inviteCode, string userId, string name)
        {
            var url = $"{_baseUrl}/join?invite_code={Uri.EscapeDataString(inviteCode)}&user_id={Uri.EscapeDataString(userId)}&name={Uri.EscapeDataString(name)}";
            return await _apiClient.PostAsync<Dictionary<string, object>>(url, null)
                ?? new Dictionary<string, object>();
        }

        public async Task<Dictionary<string, object>> AddMemberAsync(string groupId, string userId, string name, string role = "member")
        {
            var request = new
            {
                group_id = groupId,
                user_id = userId,
                name = name,
                role = role
            };

            return await _apiClient.PostAsync<Dictionary<string, object>>(
                $"{_baseUrl}/groups/{groupId}/members",
                request
            ) ?? new Dictionary<string, object>();
        }

        public async Task<Dictionary<string, object>> RemoveMemberAsync(string groupId, string userId, string operatorId)
        {
            var url = $"{_baseUrl}/groups/{groupId}/members/{userId}?operator_id={Uri.EscapeDataString(operatorId)}";
            return await _apiClient.DeleteAsync<Dictionary<string, object>>(url)
                ?? new Dictionary<string, object>();
        }

        public async Task<Dictionary<string, object>> ShareLocationAsync(string groupId, LocationShareRequest request)
        {
            var url = $"{_baseUrl}/location/share?user_id={Uri.EscapeDataString(request.UserId)}";
            return await _apiClient.PostAsync<Dictionary<string, object>>(url, request)
                ?? new Dictionary<string, object>();
        }

        public async Task<List<MemberLocation>> GetMemberLocationsAsync(string groupId)
        {
            var result = await _apiClient.GetAsync<List<MemberLocation>>(
                $"{_baseUrl}/groups/{groupId}/location/members"
            );
            return result ?? new List<MemberLocation>();
        }

        public async Task<Dictionary<string, object>> CreateSharedScheduleAsync(SharedScheduleCreate request)
        {
            return await _apiClient.PostAsync<Dictionary<string, object>>(
                $"{_baseUrl}/calendar/shared",
                request
            ) ?? new Dictionary<string, object>();
        }

        public async Task<List<SharedSchedule>> GetSharedSchedulesAsync(string groupId, string? startDate = null, string? endDate = null)
        {
            var url = $"{_baseUrl}/groups/{groupId}/calendar/shared";
            var params_list = new List<string>();
            
            if (!string.IsNullOrEmpty(startDate))
                params_list.Add($"start_date={Uri.EscapeDataString(startDate)}");
            if (!string.IsNullOrEmpty(endDate))
                params_list.Add($"end_date={Uri.EscapeDataString(endDate)}");
            
            if (params_list.Count > 0)
                url += "?" + string.Join("&", params_list);

            var result = await _apiClient.GetAsync<List<SharedSchedule>>(url);
            return result ?? new List<SharedSchedule>();
        }
    }
}