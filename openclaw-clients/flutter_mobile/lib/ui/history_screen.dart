import 'package:flutter/material.dart';
import '../core/conversation/conversation_manager.dart';

/// 历史记录页面
class HistoryScreen extends StatelessWidget {
  final ConversationManager conversationManager;
  final Function(ConversationManager.ChatSession) onLoadSession;

  const HistoryScreen({
    super.key,
    required this.conversationManager,
    required this.onLoadSession,
  });

  @override
  Widget build(BuildContext context) {
    final history = conversationManager.getHistory();

    return Scaffold(
      appBar: AppBar(
        title: const Text('📜 对话历史'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline),
            onPressed: () async {
              final confirmed = await showDialog<bool>(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('确认清空'),
                  content: const Text('确定要清空所有历史记录吗？'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context, false),
                      child: const Text('取消'),
                    ),
                    TextButton(
                      onPressed: () => Navigator.pop(context, true),
                      child: const Text('清空', style: TextStyle(color: Colors.red)),
                    ),
                  ],
                ),
              );

              if (confirmed == true) {
                await conversationManager.clearHistory();
                if (context.mounted) Navigator.pop(context);
              }
            },
          ),
        ],
      ),
      body: history.isEmpty
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.history, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('暂无历史记录', style: TextStyle(color: Colors.grey, fontSize: 16)),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: history.length,
              itemBuilder: (context, index) {
                final session = history[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    title: Text(
                      session.preview,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(
                      '${_formatDate(session.timestamp)} · ${session.messages.length} 条消息',
                      style: TextStyle(color: Colors.grey[600], fontSize: 12),
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _showLoadDialog(context, session),
                  ),
                );
              },
            ),
    );
  }

  void _showLoadDialog(BuildContext context, ConversationManager.ChatSession session) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('加载历史对话'),
        content: Text('确定要加载这段对话吗？当前对话将被替换。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () {
              onLoadSession(session);
              Navigator.pop(context);
              Navigator.pop(context);
            },
            child: const Text('加载'),
          ),
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inDays == 0) {
      return '今天 ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } else if (diff.inDays == 1) {
      return '昨天';
    } else if (diff.inDays < 7) {
      return '${diff.inDays} 天前';
    } else {
      return '${date.month}/${date.day}';
    }
  }
}
