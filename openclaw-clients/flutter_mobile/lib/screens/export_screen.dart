import 'package:flutter/material.dart';
import '../services/export_service.dart';

class ExportScreen extends StatelessWidget {
  final ExportService _exportService = ExportService();
  
  ExportScreen({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('数据导出'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            '健康报告',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          _buildExportCard(
            context,
            icon: Icons.picture_as_pdf,
            title: '健康报告 PDF',
            subtitle: '包含步数、心率、睡眠等健康数据',
            color: Colors.red,
            onTap: () => _exportHealthPdf(context),
          ),
          
          const SizedBox(height: 24),
          const Text(
            '财务报告',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          _buildExportCard(
            context,
            icon: Icons.table_chart,
            title: '财务报告 Excel',
            subtitle: '包含收支明细、分类统计',
            color: Colors.green,
            onTap: () => _exportFinanceExcel(context),
          ),
          
          const SizedBox(height: 24),
          const Text(
            '完整数据',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          _buildExportCard(
            context,
            icon: Icons.data_object,
            title: '完整数据 JSON',
            subtitle: '导出所有数据，可用于备份或迁移',
            color: Colors.blue,
            onTap: () => _exportDataJson(context),
          ),
          
          const SizedBox(height: 32),
          const Divider(),
          const SizedBox(height: 16),
          
          const Text(
            '说明',
            style: TextStyle(fontSize: 14, color: Colors.grey),
          ),
          const SizedBox(height: 8),
          const Text(
            '• 导出的文件将保存在应用文档目录\n'
            '• 可以通过系统分享功能发送到其他应用\n'
            '• 所有数据仅保存在本地，保护您的隐私',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],
      ),
    );
  }
  
  Widget _buildExportCard(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      child: ListTile(
        leading: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: color),
        ),
        title: Text(title),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
  
  Future<void> _exportHealthPdf(BuildContext context) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const AlertDialog(
        content: Row(
          children: [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Text('正在生成PDF...'),
          ],
        ),
      ),
    );
    
    final success = await _exportService.exportHealthPdf();
    
    if (context.mounted) {
      Navigator.pop(context);
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? '健康报告已生成' : '导出失败'),
        ),
      );
    }
  }
  
  Future<void> _exportFinanceExcel(BuildContext context) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const AlertDialog(
        content: Row(
          children: [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Text('正在生成Excel...'),
          ],
        ),
      ),
    );
    
    final success = await _exportService.exportFinanceExcel();
    
    if (context.mounted) {
      Navigator.pop(context);
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success ? '财务报告已生成' : '导出失败'),
        ),
      );
    }
  }
  
  Future<void> _exportDataJson(BuildContext context) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const AlertDialog(
        content: Row(
          children: [
            CircularProgressIndicator(),
            SizedBox(width: 16),
            Text('正在导出数据...'),
          ],
        ),
      ),
    );
    
    final data = await _exportService.exportDataJson();
    
    if (context.mounted) {
      Navigator.pop(context);
      
      if (data != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('数据已导出')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('导出失败')),
        );
      }
    }
  }
}