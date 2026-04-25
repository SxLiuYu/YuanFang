import 'package:flutter/material.dart';
import 'api_client.dart';

class AccountingResult {
  final double amount;
  final String category;
  final String type;
  final String date;
  final String description;
  final String? merchant;
  final double confidence;
  
  AccountingResult({
    required this.amount,
    required this.category,
    required this.type,
    required this.date,
    required this.description,
    this.merchant,
    this.confidence = 1.0,
  });
  
  factory AccountingResult.fromJson(Map<String, dynamic> json) {
    return AccountingResult(
      amount: (json['amount'] ?? 0).toDouble(),
      category: json['category'] ?? '其他',
      type: json['type'] ?? 'expense',
      date: json['date'] ?? '',
      description: json['description'] ?? '',
      merchant: json['merchant'],
      confidence: (json['confidence'] ?? 1.0).toDouble(),
    );
  }
}

class NaturalLanguageAccountingService {
  final OpenClawApiClient _apiClient = OpenClawApiClient();
  
  // 解析自然语言
  Future<AccountingResult?> parse(String text) async {
    try {
      final response = await _apiClient.post(
        '/api/v1/accounting/parse',
        {'text': text},
      );
      
      if (response['success'] == true) {
        return AccountingResult.fromJson(response['data']);
      }
      return null;
    } catch (e) {
      debugPrint('Parse accounting error: $e');
      return null;
    }
  }
  
  // 快速记账（解析+保存）
  Future<Map<String, dynamic>?> quickRecord(String text) async {
    try {
      final response = await _apiClient.post(
        '/api/v1/accounting/quick-record',
        {'text': text},
      );
      
      if (response['success'] == true) {
        return response['data'];
      }
      return null;
    } catch (e) {
      debugPrint('Quick record error: $e');
      return null;
    }
  }
  
  // 本地解析（离线模式）
  AccountingResult? parseLocally(String text) {
    // 简单的正则匹配
    final amountRegex = RegExp(r'(\d+(?:\.\d+)?)\s*(?:元|块|¥)');
    final match = amountRegex.firstMatch(text);
    
    if (match == null) return null;
    
    final amount = double.tryParse(match.group(1) ?? '0') ?? 0;
    
    // 分类判断
    String category = '其他';
    if (text.contains('饭') || text.contains('餐') || text.contains('外卖')) {
      category = '餐饮';
    } else if (text.contains('打车') || text.contains('滴滴') || text.contains('地铁')) {
      category = '交通';
    } else if (text.contains('买') || text.contains('购物')) {
      category = '购物';
    } else if (text.contains('工资') || text.contains('收入')) {
      category = '收入';
    }
    
    // 类型判断
    String type = 'expense';
    if (text.contains('收') || text.contains('工资') || text.contains('到账')) {
      type = 'income';
    }
    
    return AccountingResult(
      amount: amount,
      category: category,
      type: type,
      date: DateTime.now().toString().split(' ')[0],
      description: text,
    );
  }
}