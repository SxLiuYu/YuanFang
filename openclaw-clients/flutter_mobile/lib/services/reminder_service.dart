import 'dart:convert';
import 'package:flutter/material.dart';
import 'api_client.dart';

class Reminder {
  final String reminderId;
  final String title;
  final String description;
  final String reminderType;
  final String priority;
  final DateTime? triggerTime;
  final bool isActive;
  final bool isTriggered;
  
  Reminder({
    required this.reminderId,
    required this.title,
    this.description = '',
    required this.reminderType,
    this.priority = 'normal',
    this.triggerTime,
    this.isActive = true,
    this.isTriggered = false,
  });
  
  factory Reminder.fromJson(Map<String, dynamic> json) {
    return Reminder(
      reminderId: json['reminder_id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      reminderType: json['reminder_type'] ?? 'time',
      priority: json['priority'] ?? 'normal',
      triggerTime: json['trigger_time'] != null 
          ? DateTime.parse(json['trigger_time']) 
          : null,
      isActive: json['is_active'] == 1,
      isTriggered: json['is_triggered'] == 1,
    );
  }
}

class ReminderService extends ChangeNotifier {
  final OpenClawApiClient _apiClient = OpenClawApiClient();
  
  List<Reminder> _reminders = [];
  List<Reminder> _pendingReminders = [];
  bool _isLoading = false;
  
  List<Reminder> get reminders => _reminders;
  List<Reminder> get pendingReminders => _pendingReminders;
  bool get isLoading => _isLoading;
  
  // 创建提醒
  Future<bool> createReminder({
    required String title,
    String type = 'time',
    DateTime? triggerTime,
    String description = '',
    String priority = 'normal',
  }) async {
    try {
      final response = await _apiClient.post('/api/v1/reminder/create', {
        'title': title,
        'reminder_type': type,
        'trigger_time': triggerTime?.toIso8601String(),
        'description': description,
        'priority': priority,
      });
      
      if (response['success'] == true) {
        await fetchReminders();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Create reminder error: $e');
      return false;
    }
  }
  
  // 创建用药提醒
  Future<bool> createMedicationReminder({
    required String medication,
    required List<String> times,
    List<String>? days,
  }) async {
    try {
      final response = await _apiClient.post('/api/v1/reminder/medication', {
        'medication': medication,
        'times': times,
        'days': days,
      });
      
      if (response['success'] == true) {
        await fetchReminders();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Create medication reminder error: $e');
      return false;
    }
  }
  
  // 获取提醒列表
  Future<void> fetchReminders({bool activeOnly = true}) async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await _apiClient.get(
        '/api/v1/reminder/list',
        {'active_only': activeOnly.toString()},
      );
      
      if (response['success'] == true) {
        final data = response['data'] as List;
        _reminders = data.map((json) => Reminder.fromJson(json)).toList();
      }
    } catch (e) {
      debugPrint('Fetch reminders error: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // 获取待触发提醒
  Future<void> fetchPendingReminders() async {
    try {
      final response = await _apiClient.get('/api/v1/reminder/pending', {});
      
      if (response['success'] == true) {
        final data = response['data'] as List;
        _pendingReminders = data.map((json) => Reminder.fromJson(json)).toList();
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Fetch pending reminders error: $e');
    }
  }
  
  // 获取即将到来的提醒
  Future<List<Reminder>> getUpcomingReminders({int hours = 24}) async {
    try {
      final response = await _apiClient.get(
        '/api/v1/reminder/upcoming',
        {'hours': hours.toString()},
      );
      
      if (response['success'] == true) {
        final data = response['data'] as List;
        return data.map((json) => Reminder.fromJson(json)).toList();
      }
    } catch (e) {
      debugPrint('Get upcoming reminders error: $e');
    }
    return [];
  }
  
  // 触发提醒
  Future<bool> triggerReminder(String reminderId) async {
    try {
      final response = await _apiClient.post(
        '/api/v1/reminder/$reminderId/trigger',
        {},
      );
      return response['success'] == true;
    } catch (e) {
      debugPrint('Trigger reminder error: $e');
      return false;
    }
  }
  
  // 推迟提醒
  Future<bool> snoozeReminder(String reminderId, {int minutes = 10}) async {
    try {
      final response = await _apiClient.post(
        '/api/v1/reminder/$reminderId/snooze?minutes=$minutes',
        {},
      );
      
      if (response['success'] == true) {
        await fetchPendingReminders();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Snooze reminder error: $e');
      return false;
    }
  }
  
  // 完成提醒
  Future<bool> completeReminder(String reminderId) async {
    try {
      final response = await _apiClient.post(
        '/api/v1/reminder/$reminderId/complete',
        {},
      );
      
      if (response['success'] == true) {
        await fetchReminders();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Complete reminder error: $e');
      return false;
    }
  }
  
  // 删除提醒
  Future<bool> deleteReminder(String reminderId) async {
    try {
      final response = await _apiClient.delete(
        '/api/v1/reminder/$reminderId',
        {},
      );
      
      if (response['success'] == true) {
        await fetchReminders();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Delete reminder error: $e');
      return false;
    }
  }
  
  // 检查位置触发
  Future<List<Reminder>> checkLocationTriggers(double lat, double lng) async {
    try {
      final response = await _apiClient.post('/api/v1/reminder/check-location', {
        'latitude': lat,
        'longitude': lng,
      });
      
      if (response['success'] == true) {
        final data = response['data'] as List;
        return data.map((json) => Reminder.fromJson(json)).toList();
      }
    } catch (e) {
      debugPrint('Check location triggers error: $e');
    }
    return [];
  }
  
  // 获取提醒建议
  Future<List<Map<String, dynamic>>> getSuggestions() async {
    try {
      final response = await _apiClient.get('/api/v1/reminder/suggestions', {});
      
      if (response['success'] == true) {
        return List<Map<String, dynamic>>.from(response['data']);
      }
    } catch (e) {
      debugPrint('Get suggestions error: $e');
    }
    return [];
  }
}