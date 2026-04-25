import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:dio/dio.dart';

class OpenClawApiClient {
  static final OpenClawApiClient _instance = OpenClawApiClient._internal();
  factory OpenClawApiClient() => _instance;
  OpenClawApiClient._internal();
  
  late Dio _dio;
  String _baseUrl = 'http://localhost:8082';
  
  Future<void> initialize({String? baseUrl}) async {
    if (baseUrl != null) {
      _baseUrl = baseUrl;
    }
    
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));
  }
  
  Future<Map<String, dynamic>> healthCheck() async {
    try {
      final response = await _dio.get('/health');
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
  
  // ========== 位置数据 ==========
  
  Future<Map<String, dynamic>> syncLocation({
    required double latitude,
    required double longitude,
    double? accuracy,
  }) async {
    try {
      final response = await _dio.post('/api/v1/personal/location', data: {
        'latitude': latitude,
        'longitude': longitude,
        'accuracy': accuracy ?? 10.0,
        'timestamp': DateTime.now().toIso8601String(),
      });
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
  
  // ========== 健康数据 ==========
  
  Future<Map<String, dynamic>> syncHealth({
    int? steps,
    int? heartRate,
    double? sleepHours,
    int? calories,
  }) async {
    try {
      final data = <String, dynamic>{
        'timestamp': DateTime.now().toIso8601String(),
      };
      
      if (steps != null) data['steps'] = steps;
      if (heartRate != null) data['heart_rate'] = heartRate;
      if (sleepHours != null) data['sleep_hours'] = sleepHours;
      if (calories != null) data['calories'] = calories;
      
      final response = await _dio.post('/api/v1/health/metrics/record', data: data);
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
  
  // ========== 财务数据 ==========
  
  Future<Map<String, dynamic>> syncPayment({
    required double amount,
    required String merchant,
    String? category,
    String type = 'expense',
  }) async {
    try {
      final response = await _dio.post('/api/v1/finance/transaction/add', data: {
        'amount': amount,
        'category': category ?? _autoCategorize(merchant),
        'type': type,
        'description': merchant,
        'source': 'mobile_sync',
      });
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
  
  String _autoCategorize(String merchant) {
    final merchantLower = merchant.toLowerCase();
    
    if (merchantLower.contains('美团') || merchantLower.contains('饿了么') ||
        merchantLower.contains('餐厅') || merchantLower.contains('咖啡')) {
      return '餐饮';
    }
    if (merchantLower.contains('滴滴') || merchantLower.contains('加油') ||
        merchantLower.contains('停车')) {
      return '交通';
    }
    if (merchantLower.contains('淘宝') || merchantLower.contains('京东') ||
        merchantLower.contains('超市')) {
      return '购物';
    }
    
    return '其他';
  }
  
  // ========== 日程数据 ==========
  
  Future<Map<String, dynamic>> syncCalendar({
    required String title,
    required String date,
    String? time,
    String? location,
  }) async {
    try {
      String startTime = date;
      if (time != null) {
        startTime = '$date${'T'}$time:00';
      }
      
      final response = await _dio.post('/api/v1/calendar/event/create', data: {
        'title': title,
        'start_time': startTime,
        'location': location,
        'source': 'mobile_sync',
      });
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
  
  // ========== AI对话 ==========
  
  Future<Map<String, dynamic>> chat({
    required String message,
    String? sessionId,
  }) async {
    try {
      final data = <String, dynamic>{
        'message': message,
        'voice_output': false,
      };
      
      if (sessionId != null) {
        data['session_id'] = sessionId;
      }
      
      final response = await _dio.post('/api/v1/agent/chat', data: data);
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
  
  // ========== 报告 ==========
  
  Future<Map<String, dynamic>> getReport(String type) async {
    try {
      final response = await _dio.get('/api/v1/report/$type');
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
  
  // ========== 财务报告 ==========
  
  Future<Map<String, dynamic>> getFinanceReport(String period) async {
    try {
      final response = await _dio.get('/api/v1/finance/report/$period');
      return response.data;
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
}