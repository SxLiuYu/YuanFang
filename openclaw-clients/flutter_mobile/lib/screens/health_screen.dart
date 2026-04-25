import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/data_sync_service.dart';

class HealthScreen extends StatelessWidget {
  const HealthScreen({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Consumer<DataSyncService>(
      builder: (context, syncService, child) {
        final healthData = syncService.healthHistory.isNotEmpty
            ? syncService.healthHistory.last
            : null;
        
        return Scaffold(
          appBar: AppBar(
            title: const Text('健康数据'),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => syncService.fetchHealthData(),
              ),
            ],
          ),
          body: healthData == null
              ? const Center(child: Text('暂无健康数据'))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _buildStatCard(
                      icon: Icons.directions_walk,
                      title: '今日步数',
                      value: healthData.steps?.toString() ?? '--',
                      unit: '步',
                      color: Colors.blue,
                      progress: (healthData.steps ?? 0) / 10000,
                    ),
                    const SizedBox(height: 16),
                    _buildStatCard(
                      icon: Icons.favorite,
                      title: '当前心率',
                      value: healthData.heartRate?.toString() ?? '--',
                      unit: 'bpm',
                      color: Colors.red,
                    ),
                    const SizedBox(height: 16),
                    _buildStatCard(
                      icon: Icons.bedtime,
                      title: '昨晚睡眠',
                      value: healthData.sleepHours?.toStringAsFixed(1) ?? '--',
                      unit: '小时',
                      color: Colors.purple,
                    ),
                    const SizedBox(height: 16),
                    _buildStatCard(
                      icon: Icons.local_fire_department,
                      title: '消耗卡路里',
                      value: healthData.calories?.toString() ?? '--',
                      unit: 'kcal',
                      color: Colors.orange,
                    ),
                  ],
                ),
        );
      },
    );
  }
  
  Widget _buildStatCard({
    required IconData icon,
    required String title,
    required String value,
    required String unit,
    required Color color,
    double? progress,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(icon, color: color),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(color: Colors.grey[600]),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            value,
                            style: const TextStyle(
                              fontSize: 32,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Text(unit),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (progress != null) ...[
              const SizedBox(height: 16),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: progress.clamp(0.0, 1.0),
                  backgroundColor: color.withOpacity(0.1),
                  valueColor: AlwaysStoppedAnimation(color),
                  minHeight: 8,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}