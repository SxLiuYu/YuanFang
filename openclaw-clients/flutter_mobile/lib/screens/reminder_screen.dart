import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/reminder_service.dart';

class ReminderScreen extends StatefulWidget {
  const ReminderScreen({super.key});
  
  @override
  State<ReminderScreen> createState() => _ReminderScreenState();
}

class _ReminderScreenState extends State<ReminderScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ReminderService>().fetchReminders();
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('提醒'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showCreateDialog(),
          ),
        ],
      ),
      body: Consumer<ReminderService>(
        builder: (context, service, child) {
          if (service.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          
          if (service.reminders.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.notifications_none, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('暂无提醒', style: TextStyle(color: Colors.grey)),
                ],
              ),
            );
          }
          
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: service.reminders.length,
            itemBuilder: (context, index) {
              final reminder = service.reminders[index];
              return _buildReminderCard(service, reminder);
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateDialog(),
        icon: const Icon(Icons.add),
        label: const Text('新建提醒'),
      ),
    );
  }
  
  Widget _buildReminderCard(ReminderService service, Reminder reminder) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _getTypeColor(reminder.reminderType),
          child: Icon(_getTypeIcon(reminder.reminderType), color: Colors.white),
        ),
        title: Text(
          reminder.title,
          style: TextStyle(
            decoration: reminder.isTriggered ? TextDecoration.lineThrough : null,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (reminder.description.isNotEmpty)
              Text(reminder.description),
            if (reminder.triggerTime != null)
              Text(
                '时间: ${_formatTime(reminder.triggerTime!)}',
                style: TextStyle(color: Colors.grey[600], fontSize: 12),
              ),
          ],
        ),
        trailing: PopupMenuButton<String>(
          onSelected: (value) => _handleAction(service, reminder.reminderId, value),
          itemBuilder: (context) => [
            const PopupMenuItem(value: 'complete', child: Text('完成')),
            const PopupMenuItem(value: 'snooze', child: Text('推迟10分钟')),
            const PopupMenuItem(value: 'delete', child: Text('删除')),
          ],
        ),
      ),
    );
  }
  
  Color _getTypeColor(String type) {
    switch (type) {
      case 'time': return Colors.blue;
      case 'location': return Colors.green;
      case 'medication': return Colors.red;
      case 'budget': return Colors.orange;
      case 'habit': return Colors.purple;
      default: return Colors.grey;
    }
  }
  
  IconData _getTypeIcon(String type) {
    switch (type) {
      case 'time': return Icons.access_time;
      case 'location': return Icons.location_on;
      case 'medication': return Icons.medication;
      case 'budget': return Icons.account_balance_wallet;
      case 'habit': return Icons.repeat;
      default: return Icons.notifications;
    }
  }
  
  String _formatTime(DateTime time) {
    return '${time.month}/${time.day} ${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }
  
  Future<void> _handleAction(ReminderService service, String id, String action) async {
    switch (action) {
      case 'complete':
        await service.completeReminder(id);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('提醒已完成')),
          );
        }
        break;
      case 'snooze':
        await service.snoozeReminder(id);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('已推迟10分钟')),
          );
        }
        break;
      case 'delete':
        await service.deleteReminder(id);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('提醒已删除')),
          );
        }
        break;
    }
  }
  
  void _showCreateDialog() {
    showDialog(
      context: context,
      builder: (context) => _CreateReminderDialog(),
    );
  }
}

class _CreateReminderDialog extends StatefulWidget {
  @override
  State<_CreateReminderDialog> createState() => _CreateReminderDialogState();
}

class _CreateReminderDialogState extends State<_CreateReminderDialog> {
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  String _type = 'time';
  DateTime? _triggerTime;
  
  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('新建提醒'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _titleController,
              decoration: const InputDecoration(
                labelText: '标题',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _type,
              decoration: const InputDecoration(
                labelText: '类型',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'time', child: Text('定时提醒')),
                DropdownMenuItem(value: 'location', child: Text('位置提醒')),
                DropdownMenuItem(value: 'medication', child: Text('用药提醒')),
                DropdownMenuItem(value: 'habit', child: Text('习惯提醒')),
              ],
              onChanged: (value) {
                setState(() => _type = value ?? 'time');
              },
            ),
            if (_type == 'time') ...[
              const SizedBox(height: 16),
              ListTile(
                title: Text(_triggerTime == null
                    ? '选择时间'
                    : '时间: ${_triggerTime.toString()}'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () async {
                  final time = await showTimePicker(
                    context: context,
                    initialTime: TimeOfDay.now(),
                  );
                  if (time != null) {
                    setState(() {
                      _triggerTime = DateTime(
                        DateTime.now().year,
                        DateTime.now().month,
                        DateTime.now().day,
                        time.hour,
                        time.minute,
                      );
                    });
                  }
                },
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('取消'),
        ),
        ElevatedButton(
          onPressed: () async {
            if (_titleController.text.isEmpty) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('请输入标题')),
              );
              return;
            }
            
            final service = context.read<ReminderService>();
            final success = await service.createReminder(
              title: _titleController.text,
              type: _type,
              triggerTime: _triggerTime,
              description: _descriptionController.text,
            );
            
            if (success && mounted) {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('提醒已创建')),
              );
            }
          },
          child: const Text('创建'),
        ),
      ],
    );
  }
}