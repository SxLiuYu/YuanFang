import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'api_client.dart';

class ExportService {
  final OpenClawApiClient _apiClient = OpenClawApiClient();
  
  // 导出健康报告PDF
  Future<bool> exportHealthPdf({int days = 30}) async {
    try {
      final response = await _apiClient.getRaw(
        '/api/v1/export/health/pdf?days=$days',
      );
      
      if (response != null) {
        final bytes = await response.bytes();
        await _saveAndShare(
          bytes,
          'health_report.pdf',
          '健康报告已生成',
        );
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Export health PDF error: $e');
      return false;
    }
  }
  
  // 导出财务报告Excel
  Future<bool> exportFinanceExcel({String? month}) async {
    try {
      final url = month != null
          ? '/api/v1/export/finance/excel?month=$month'
          : '/api/v1/export/finance/excel';
      
      final response = await _apiClient.getRaw(url);
      
      if (response != null) {
        final bytes = await response.bytes();
        await _saveAndShare(
          bytes,
          'finance_report.xlsx',
          '财务报告已生成',
        );
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Export finance Excel error: $e');
      return false;
    }
  }
  
  // 导出完整数据JSON
  Future<Map<String, dynamic>?> exportDataJson() async {
    try {
      final response = await _apiClient.get('/api/v1/export/data/json', {});
      
      if (response['success'] == true) {
        return response['data'];
      }
      return null;
    } catch (e) {
      debugPrint('Export data JSON error: $e');
      return null;
    }
  }
  
  // 保存并分享
  Future<void> _saveAndShare(
    Uint8List bytes,
    String fileName,
    String subject,
  ) async {
    final directory = await getApplicationDocumentsDirectory();
    final file = await XFile.fromData(
      bytes,
      name: fileName,
    );
    
    await Share.shareXFiles(
      [file],
      subject: subject,
    );
  }
  
  // 保存到本地
  Future<String?> saveToLocal(Uint8List bytes, String fileName) async {
    try {
      final directory = await getApplicationDocumentsDirectory();
      final file = await XFile.fromData(bytes, name: fileName);
      final path = '${directory.path}/$fileName';
      await file.saveTo(path);
      return path;
    } catch (e) {
      debugPrint('Save to local error: $e');
      return null;
    }
  }
}