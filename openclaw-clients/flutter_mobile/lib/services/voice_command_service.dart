import 'package:flutter/material.dart';
import 'api_client.dart';

enum VoiceIntent {
  accounting,
  query,
  reminder,
  control,
  weather,
  unknown,
}

class VoiceCommandResult {
  final VoiceIntent intent;
  final Map<String, dynamic> slots;
  final String originalText;
  final double confidence;
  
  VoiceCommandResult({
    required this.intent,
    required this.slots,
    required this.originalText,
    this.confidence = 1.0,
  });
  
  factory VoiceCommandResult.fromJson(Map<String, dynamic> json) {
    return VoiceCommandResult(
      intent: _parseIntent(json['intent']),
      slots: json['slots'] ?? {},
      originalText: json['original_text'] ?? '',
      confidence: (json['confidence'] ?? 1.0).toDouble(),
    );
  }
  
  static VoiceIntent _parseIntent(String? intent) {
    switch (intent) {
      case 'accounting': return VoiceIntent.accounting;
      case 'query': return VoiceIntent.query;
      case 'reminder': return VoiceIntent.reminder;
      case 'control': return VoiceIntent.control;
      case 'weather': return VoiceIntent.weather;
      default: return VoiceIntent.unknown;
    }
  }
}

class VoiceCommandService extends ChangeNotifier {
  final OpenClawApiClient _apiClient = OpenClawApiClient();
  
  VoiceCommandResult? _lastResult;
  bool _isProcessing = false;
  
  VoiceCommandResult? get lastResult => _lastResult;
  bool get isProcessing => _isProcessing;
  
  // 解析语音命令
  Future<VoiceCommandResult?> parseCommand(String text) async {
    _isProcessing = true;
    notifyListeners();
    
    try {
      final response = await _apiClient.post('/api/v1/voice/parse', {'text': text});
      
      if (response['success'] == true) {
        _lastResult = VoiceCommandResult.fromJson(response['data']);
        return _lastResult;
      }
      return null;
    } catch (e) {
      debugPrint('Parse voice command error: $e');
      return null;
    } finally {
      _isProcessing = false;
      notifyListeners();
    }
  }
  
  // 解析并执行命令
  Future<Map<String, dynamic>?> parseAndExecute(String text) async {
    try {
      final response = await _apiClient.post('/api/v1/voice/execute', {'text': text});
      
      if (response['success'] == true) {
        _lastResult = VoiceCommandResult.fromJson(response['data']['parsed']);
        notifyListeners();
        return response['data'];
      }
      return null;
    } catch (e) {
      debugPrint('Execute voice command error: $e');
      return null;
    }
  }
  
  // 本地解析（离线模式）
  VoiceCommandResult parseLocally(String text) {
    final textLower = text.toLowerCase();
    
    // 意图识别
    VoiceIntent intent = VoiceIntent.unknown;
    Map<String, dynamic> slots = {};
    
    // 记账意图
    if (textLower.contains('记') || textLower.contains('花') || textLower.contains('块')) {
      intent = VoiceIntent.accounting;
      
      // 提取金额
      final amountRegex = RegExp(r'(\d+(?:\.\d+)?)');
      final match = amountRegex.firstMatch(text);
      if (match != null) {
        slots['amount'] = double.tryParse(match.group(1) ?? '0');
      }
      
      // 分类
      if (textLower.contains('饭') || textLower.contains('餐')) {
        slots['category'] = '餐饮';
      } else if (textLower.contains('打车') || textLower.contains('滴滴')) {
        slots['category'] = '交通';
      }
    }
    
    // 查询意图
    else if (textLower.contains('查') || textLower.contains('多少')) {
      intent = VoiceIntent.query;
      
      if (textLower.contains('支出') || textLower.contains('花')) {
        slots['query_type'] = 'expense';
      } else if (textLower.contains('收入')) {
        slots['query_type'] = 'income';
      }
    }
    
    // 提醒意图
    else if (textLower.contains('提醒') || textLower.contains('叫我')) {
      intent = VoiceIntent.reminder;
      slots['content'] = text.replaceAll(RegExp(r'提醒我?|叫我'), '').trim();
    }
    
    // 控制意图
    else if (textLower.contains('打开') || textLower.contains('关闭') || textLower.contains('开灯') || textLower.contains('关灯')) {
      intent = VoiceIntent.control;
      
      if (textLower.contains('开')) {
        slots['action'] = 'turn_on';
      } else if (textLower.contains('关')) {
        slots['action'] = 'turn_off';
      }
      
      // 设备
      if (textLower.contains('灯')) {
        slots['device'] = 'light';
      } else if (textLower.contains('空调')) {
        slots['device'] = 'ac';
      }
    }
    
    // 天气意图
    else if (textLower.contains('天气')) {
      intent = VoiceIntent.weather;
    }
    
    return VoiceCommandResult(
      intent: intent,
      slots: slots,
      originalText: text,
    );
  }
}