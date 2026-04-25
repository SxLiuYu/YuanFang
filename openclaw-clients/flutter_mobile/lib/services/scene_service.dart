import 'package:flutter/material.dart';
import 'api_client.dart';

enum SceneType { home, away, sleep, work }
enum TriggerType { location, time, event }

class AutomationRule {
  final String ruleId;
  final String ruleName;
  final SceneType sceneType;
  final TriggerType triggerType;
  final Map<String, dynamic> triggerConfig;
  final List<Map<String, dynamic>> actions;
  final bool isActive;
  
  AutomationRule({
    required this.ruleId,
    required this.ruleName,
    required this.sceneType,
    required this.triggerType,
    required this.triggerConfig,
    required this.actions,
    this.isActive = true,
  });
  
  factory AutomationRule.fromJson(Map<String, dynamic> json) {
    return AutomationRule(
      ruleId: json['rule_id'] ?? '',
      ruleName: json['rule_name'] ?? '',
      sceneType: _parseSceneType(json['scene_type']),
      triggerType: _parseTriggerType(json['trigger_type']),
      triggerConfig: _parseJson(json['trigger_config']),
      actions: _parseActions(json['actions']),
      isActive: json['is_active'] == 1,
    );
  }
  
  static SceneType _parseSceneType(String? type) {
    switch (type) {
      case 'home': return SceneType.home;
      case 'away': return SceneType.away;
      case 'sleep': return SceneType.sleep;
      case 'work': return SceneType.work;
      default: return SceneType.home;
    }
  }
  
  static TriggerType _parseTriggerType(String? type) {
    switch (type) {
      case 'location': return TriggerType.location;
      case 'time': return TriggerType.time;
      case 'event': return TriggerType.event;
      default: return TriggerType.location;
    }
  }
  
  static Map<String, dynamic> _parseJson(dynamic data) {
    if (data is String) {
      try {
        return Map<String, dynamic>.from(Uri.splitQueryString(data));
      } catch (_) {
        return {};
      }
    }
    return Map<String, dynamic>.from(data ?? {});
  }
  
  static List<Map<String, dynamic>> _parseActions(dynamic data) {
    if (data is String) {
      try {
        return [];
      } catch (_) {
        return [];
      }
    }
    return List<Map<String, dynamic>>.from(data ?? []);
  }
}

class SceneService extends ChangeNotifier {
  final OpenClawApiClient _apiClient = OpenClawApiClient();
  
  List<AutomationRule> _rules = [];
  List<Map<String, dynamic>> _templates = [];
  bool _isLoading = false;
  
  List<AutomationRule> get rules => _rules;
  List<Map<String, dynamic>> get templates => _templates;
  bool get isLoading => _isLoading;
  
  // 获取规则列表
  Future<void> fetchRules({bool activeOnly = true}) async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await _apiClient.get(
        '/api/v1/scene/rules',
        {'active_only': activeOnly.toString()},
      );
      
      if (response['success'] == true) {
        final data = response['data'] as List;
        _rules = data.map((json) => AutomationRule.fromJson(json)).toList();
      }
    } catch (e) {
      debugPrint('Fetch rules error: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // 创建规则
  Future<bool> createRule({
    required String name,
    required String sceneType,
    required String triggerType,
    required Map<String, dynamic> triggerConfig,
    required List<Map<String, dynamic>> actions,
  }) async {
    try {
      final response = await _apiClient.post('/api/v1/scene/rules', {
        'name': name,
        'scene_type': sceneType,
        'trigger_type': triggerType,
        'trigger_config': triggerConfig,
        'actions': actions,
      });
      
      if (response['success'] == true) {
        await fetchRules();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Create rule error: $e');
      return false;
    }
  }
  
  // 获取模板
  Future<void> fetchTemplates() async {
    try {
      final response = await _apiClient.get('/api/v1/scene/templates', {});
      
      if (response['success'] == true) {
        _templates = List<Map<String, dynamic>>.from(response['data']);
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Fetch templates error: $e');
    }
  }
  
  // 从模板创建
  Future<bool> createFromTemplate(String templateName, {Map<String, dynamic>? config}) async {
    try {
      final response = await _apiClient.post(
        '/api/v1/scene/templates/$templateName',
        config ?? {},
      );
      
      if (response['success'] == true) {
        await fetchRules();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Create from template error: $e');
      return false;
    }
  }
  
  // 激活/停用规则
  Future<bool> activateRule(String ruleId) async {
    try {
      final response = await _apiClient.post('/api/v1/scene/rules/$ruleId/activate', {});
      
      if (response['success'] == true) {
        await fetchRules();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Activate rule error: $e');
      return false;
    }
  }
  
  Future<bool> deactivateRule(String ruleId) async {
    try {
      final response = await _apiClient.post('/api/v1/scene/rules/$ruleId/deactivate', {});
      
      if (response['success'] == true) {
        await fetchRules();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Deactivate rule error: $e');
      return false;
    }
  }
  
  // 删除规则
  Future<bool> deleteRule(String ruleId) async {
    try {
      final response = await _apiClient.delete('/api/v1/scene/rules/$ruleId', {});
      
      if (response['success'] == true) {
        await fetchRules();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Delete rule error: $e');
      return false;
    }
  }
  
  // 手动触发场景
  Future<Map<String, dynamic>?> triggerScene(String sceneType) async {
    try {
      final response = await _apiClient.post('/api/v1/scene/trigger', {
        'scene_type': sceneType,
      });
      
      if (response['success'] == true) {
        return response['data'];
      }
      return null;
    } catch (e) {
      debugPrint('Trigger scene error: $e');
      return null;
    }
  }
}