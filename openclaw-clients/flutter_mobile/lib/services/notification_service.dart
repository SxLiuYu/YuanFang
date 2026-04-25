import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'api_client.dart';

enum NotificationType {
  payment,
  express,
  verificationCode,
  bankSms,
  unknown,
}

class NotificationResult {
  final NotificationType type;
  final Map<String, dynamic>? payment;
  final Map<String, dynamic>? express;
  final String? verificationCode;
  final Map<String, dynamic>? bankSms;
  
  NotificationResult({
    required this.type,
    this.payment,
    this.express,
    this.verificationCode,
    this.bankSms,
  });
  
  factory NotificationResult.fromJson(Map<String, dynamic> json) {
    return NotificationResult(
      type: _parseType(json['type']),
      payment: json['payment'],
      express: json['express'],
      verificationCode: json['verification_code']?['code'],
      bankSms: json['bank_sms'],
    );
  }
  
  static NotificationType _parseType(String? type) {
    switch (type) {
      case 'payment': return NotificationType.payment;
      case 'express': return NotificationType.express;
      case 'verification_code': return NotificationType.verificationCode;
      case 'bank_sms': return NotificationType.bankSms;
      default: return NotificationType.unknown;
    }
  }
}

class NotificationService {
  final OpenClawApiClient _apiClient = OpenClawApiClient();
  
  static const MethodChannel _channel = MethodChannel('com.openclaw/notification');
  
  // 解析通知文本
  Future<NotificationResult?> parseNotification(String text) async {
    try {
      final response = await _apiClient.post('/api/v1/notification/parse', {
        'text': text,
      });
      
      if (response['success'] == true) {
        return NotificationResult.fromJson(response['data']);
      }
      return null;
    } catch (e) {
      debugPrint('Parse notification error: $e');
      return null;
    }
  }
  
  // 解析并自动记账
  Future<bool> parseAndRecord(String text) async {
    try {
      final response = await _apiClient.post('/api/v1/notification/parse', {
        'text': text,
        'auto_record': true,
      });
      
      return response['success'] == true;
    } catch (e) {
      debugPrint('Parse and record error: $e');
      return false;
    }
  }
  
  // 提取验证码
  Future<String?> extractVerificationCode(String text) async {
    try {
      final response = await _apiClient.post(
        '/api/v1/notification/verification-code',
        {'text': text},
      );
      
      if (response['success'] == true) {
        return response['data']['code'];
      }
      return null;
    } catch (e) {
      debugPrint('Extract verification code error: $e');
      return null;
    }
  }
  
  // 启动通知监听（需要原生支持）
  Future<void> startListening() async {
    try {
      await _channel.invokeMethod('startListening');
    } on PlatformException catch (e) {
      debugPrint('Start notification listening error: $e');
    }
  }
  
  // 停止通知监听
  Future<void> stopListening() async {
    try {
      await _channel.invokeMethod('stopListening');
    } on PlatformException catch (e) {
      debugPrint('Stop notification listening error: $e');
    }
  }
  
  // 请求通知权限
  Future<bool> requestPermission() async {
    try {
      final result = await _channel.invokeMethod('requestPermission');
      return result == true;
    } on PlatformException catch (e) {
      debugPrint('Request notification permission error: $e');
      return false;
    }
  }
  
  // 设置通知回调
  void setNotificationCallback(Function(NotificationResult) onNotification) {
    _channel.setMethodCallHandler((call) async {
      if (call.method == 'onNotification') {
        final text = call.arguments as String;
        final result = await parseNotification(text);
        if (result != null) {
          onNotification(result);
        }
      }
    });
  }
}