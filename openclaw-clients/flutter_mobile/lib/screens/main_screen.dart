import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/data_sync_service.dart';
import '../services/api_client.dart';
import 'health_screen.dart';
import 'finance_screen.dart';
import 'location_screen.dart';
import 'chat_screen.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});
  
  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;
  
  final List<Widget> _screens = [
    const DashboardScreen(),
    const HealthScreen(),
    const FinanceScreen(),
    const ChatScreen(),
    const SettingsScreen(),
  ];
  
  @override
  void initState() {
    super.initState();
    _initializeServices();
  }
  
  Future<void> _initializeServices() async {
    final syncService = context.read<DataSyncService>();
    await syncService.initialize();
    await syncService.startLocationTracking();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: '仪表盘',
          ),
          NavigationDestination(
            icon: Icon(Icons.favorite_outline),
            selectedIcon: Icon(Icons.favorite),
            label: '健康',
          ),
          NavigationDestination(
            icon: Icon(Icons.account_balance_wallet_outlined),
            selectedIcon: Icon(Icons.account_balance_wallet),
            label: '财务',
          ),
          NavigationDestination(
            icon: Icon(Icons.chat_outlined),
            selectedIcon: Icon(Icons.chat),
            label: '对话',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: '设置',
          ),
        ],
      ),
    );
  }
}

// 仪表盘
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Consumer<DataSyncService>(
      builder: (context, syncService, child) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('OpenClaw'),
            actions: [
              IconButton(
                icon: Icon(
                  syncService.isSyncing
                      ? Icons.sync
                      : Icons.sync_outlined,
                ),
                onPressed: syncService.isSyncing
                    ? null
                    : () => syncService.syncAllData(),
              ),
            ],
          ),
          body: RefreshIndicator(
            onRefresh: () => syncService.syncAllData(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // 同步状态卡片
                _buildSyncStatusCard(syncService),
                const SizedBox(height: 16),
                
                // 健康概览
                _buildHealthOverviewCard(syncService),
                const SizedBox(height: 16),
                
                // 位置信息
                _buildLocationCard(syncService),
                const SizedBox(height: 16),
                
                // 快捷操作
                _buildQuickActionsCard(context),
              ],
            ),
          ),
        );
      },
    );
  }
  
  Widget _buildSyncStatusCard(DataSyncService syncService) {
    final lastSync = syncService.lastSyncTime;
    final statusText = lastSync != null
        ? '最后同步: ${_formatTime(lastSync)}'
        : '尚未同步';
    
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: syncService.isSyncing
              ? Colors.orange
              : Colors.green,
          child: Icon(
            syncService.isSyncing
                ? Icons.sync
                : Icons.check,
            color: Colors.white,
          ),
        ),
        title: const Text('数据同步'),
        subtitle: Text(statusText),
        trailing: syncService.isSyncing
            ? const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.chevron_right),
      ),
    );
  }
  
  Widget _buildHealthOverviewCard(DataSyncService syncService) {
    final healthData = syncService.healthHistory.isNotEmpty
        ? syncService.healthHistory.last
        : null;
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '健康概览',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildHealthItem(
                  icon: Icons.directions_walk,
                  label: '步数',
                  value: healthData?.steps?.toString() ?? '--',
                  unit: '步',
                ),
                _buildHealthItem(
                  icon: Icons.favorite,
                  label: '心率',
                  value: healthData?.heartRate?.toString() ?? '--',
                  unit: 'bpm',
                ),
                _buildHealthItem(
                  icon: Icons.bedtime,
                  label: '睡眠',
                  value: healthData?.sleepHours?.toStringAsFixed(1) ?? '--',
                  unit: '小时',
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildHealthItem({
    required IconData icon,
    required String label,
    required String value,
    required String unit,
  }) {
    return Column(
      children: [
        Icon(icon, size: 32, color: Colors.blue),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        Text(
          '$label ($unit)',
          style: TextStyle(color: Colors.grey[600]),
        ),
      ],
    );
  }
  
  Widget _buildLocationCard(DataSyncService syncService) {
    final locationData = syncService.locationHistory.isNotEmpty
        ? syncService.locationHistory.last
        : null;
    
    return Card(
      child: ListTile(
        leading: const CircleAvatar(
          backgroundColor: Colors.purple,
          child: Icon(Icons.location_on, color: Colors.white),
        ),
        title: const Text('当前位置'),
        subtitle: Text(
          locationData != null
              ? '${locationData.placeTypeString} (${locationData.latitude.toStringAsFixed(4)}, ${locationData.longitude.toStringAsFixed(4)})'
              : '未知',
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () {
          // 导航到位置详情页
        },
      ),
    );
  }
  
  Widget _buildQuickActionsCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '快捷操作',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildQuickAction(
                  icon: Icons.payment,
                  label: '记账',
                  onTap: () {
                    // 打开记账对话框
                  },
                ),
                _buildQuickAction(
                  icon: Icons.event,
                  label: '日程',
                  onTap: () {
                    // 打开日程页面
                  },
                ),
                _buildQuickAction(
                  icon: Icons.shopping_cart,
                  label: '购物',
                  onTap: () {
                    // 打开购物清单
                  },
                ),
                _buildQuickAction(
                  icon: Icons.medication,
                  label: '用药',
                  onTap: () {
                    // 打开用药提醒
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildQuickAction({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: Colors.blue.shade100,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(icon, color: Colors.blue),
          ),
          const SizedBox(height: 8),
          Text(label),
        ],
      ),
    );
  }
  
  String _formatTime(DateTime time) {
    final now = DateTime.now();
    final diff = now.difference(time);
    
    if (diff.inMinutes < 1) {
      return '刚刚';
    } else if (diff.inHours < 1) {
      return '${diff.inMinutes}分钟前';
    } else if (diff.inDays < 1) {
      return '${diff.inHours}小时前';
    } else {
      return '${diff.inDays}天前';
    }
  }
}

// 设置页面
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _serverController = TextEditingController(text: 'http://localhost:8082');
  
  @override
  void dispose() {
    _serverController.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('设置'),
      ),
      body: ListView(
        children: [
          // 服务器设置
          ListTile(
            title: const Text('服务器地址'),
            subtitle: Text(_serverController.text),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _showServerDialog(),
          ),
          const Divider(),
          
          // 数据同步设置
          const ListTile(
            title: Text('数据同步'),
            subtitle: Text('管理数据采集和同步设置'),
          ),
          SwitchListTile(
            title: const Text('位置追踪'),
            subtitle: const Text('自动记录位置变化'),
            value: true,
            onChanged: (value) {},
          ),
          SwitchListTile(
            title: const Text('健康数据'),
            subtitle: const Text('同步步数、心率等'),
            value: true,
            onChanged: (value) {},
          ),
          SwitchListTile(
            title: const Text('日程同步'),
            subtitle: const Text('同步日历事件'),
            value: true,
            onChanged: (value) {},
          ),
          const Divider(),
          
          // 隐私设置
          const ListTile(
            title: Text('隐私'),
            subtitle: Text('数据安全和隐私设置'),
          ),
          ListTile(
            title: const Text('数据存储'),
            subtitle: const Text('仅本地'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {},
          ),
          ListTile(
            title: const Text('自动清理'),
            subtitle: const Text('保留30天'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {},
          ),
          const Divider(),
          
          // 关于
          ListTile(
            title: const Text('关于'),
            subtitle: const Text('OpenClaw v1.0.0'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              showAboutDialog(
                context: context,
                applicationName: 'OpenClaw',
                applicationVersion: '1.0.0',
                applicationLegalese: '© 2025 OpenClaw',
              );
            },
          ),
        ],
      ),
    );
  }
  
  void _showServerDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('服务器地址'),
        content: TextField(
          controller: _serverController,
          decoration: const InputDecoration(
            hintText: 'http://localhost:8082',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              setState(() {});
            },
            child: const Text('确定'),
          ),
        ],
      ),
    );
  }
}