import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// 对话管理器 - 多轮对话上下文和历史记录
class ConversationManager {
  static final ConversationManager _instance = ConversationManager._internal();
  factory ConversationManager() => _instance;
  ConversationManager._internal();

  static const String _contextKey = 'conversation_context';
  static const String _historyKey = 'chat_history';
  static const int _maxContextSize = 20;
  static const int _maxHistoryCount = 50;

  List<ChatMessage> _conversationContext = [];
  List<ChatSession> _chatHistory = [];

  /// 对话消息
  class ChatMessage {
    final String id;
    final String role;
    final String content;
    final DateTime timestamp;

    ChatMessage({
      required this.role,
      required this.content,
      String? id,
      DateTime? timestamp,
    })  : id = id ?? DateTime.now().millisecondsSinceEpoch.toString(),
          timestamp = timestamp ?? DateTime.now();

    Map<String, dynamic> toJson() => {
          'id': id,
          'role': role,
          'content': content,
          'timestamp': timestamp.toIso8601String(),
        };

    factory ChatMessage.fromJson(Map<String, dynamic> json) => ChatMessage(
          id: json['id'],
          role: json['role'],
          content: json['content'],
          timestamp: DateTime.parse(json['timestamp']),
        );
  }

  /// 对话会话
  class ChatSession {
    final String id;
    final String preview;
    final DateTime timestamp;
    final List<ChatMessage> messages;

    ChatSession({
      required this.preview,
      required this.messages,
      String? id,
      DateTime? timestamp,
    })  : id = id ?? DateTime.now().millisecondsSinceEpoch.toString(),
          timestamp = timestamp ?? DateTime.now();

    Map<String, dynamic> toJson() => {
          'id': id,
          'preview': preview,
          'timestamp': timestamp.toIso8601String(),
          'messages': messages.map((m) => m.toJson()).toList(),
        };

    factory ChatSession.fromJson(Map<String, dynamic> json) => ChatSession(
          id: json['id'],
          preview: json['preview'],
          timestamp: DateTime.parse(json['timestamp']),
          messages: (json['messages'] as List)
              .map((m) => ChatMessage.fromJson(m))
              .toList(),
        );
  }

  /// 添加到上下文
  Future<void> addToContext(String role, String content) async {
    _conversationContext.add(ChatMessage(role: role, content: content));

    // 限制上下文大小
    if (_conversationContext.length > _maxContextSize) {
      _conversationContext =
          _conversationContext.sublist(_conversationContext.length - _maxContextSize);
    }

    await _saveContext();
  }

  /// 获取上下文
  List<ChatMessage> getContext() => List.unmodifiable(_conversationContext);

  /// 清空上下文
  Future<void> clearContext() async {
    _conversationContext.clear();
    await _saveContext();
  }

  /// 获取 API 用的上下文（带 system prompt）
  List<ChatMessage> getContextForAPI(int maxMessages) {
    final result = <ChatMessage>[
      ChatMessage(role: 'system', content: '你是一个家庭助手，请理解用户的语音指令并提供相应的帮助。保持对话连贯性。'),
    ];

    final start = (_conversationContext.length - maxMessages).clamp(0, _conversationContext.length);
    result.addAll(_conversationContext.sublist(start));

    return result;
  }

  /// 添加到历史
  Future<void> addToHistory(List<ChatMessage> messages) async {
    final userMessage = messages.firstWhere((m) => m.role == 'user', orElse: () => messages.first);
    final session = ChatSession(preview: userMessage.content, messages: messages);

    _chatHistory.insert(0, session);

    // 限制历史记录数量
    if (_chatHistory.length > _maxHistoryCount) {
      _chatHistory = _chatHistory.sublist(0, _maxHistoryCount);
    }

    await _saveHistory();
  }

  /// 获取历史
  List<ChatSession> getHistory() => List.unmodifiable(_chatHistory);

  /// 清空历史
  Future<void> clearHistory() async {
    _chatHistory.clear();
    await _saveHistory();
  }

  /// 保存上下文
  Future<void> _saveContext() async {
    final prefs = await SharedPreferences.getInstance();
    final json = jsonEncode(_conversationContext.map((m) => m.toJson()).toList());
    await prefs.setString(_contextKey, json);
  }

  /// 加载上下文
  Future<void> _loadContext() async {
    final prefs = await SharedPreferences.getInstance();
    final json = prefs.getString(_contextKey);
    if (json != null) {
      final list = jsonDecode(json) as List;
      _conversationContext = list.map((m) => ChatMessage.fromJson(m)).toList();
    }
  }

  /// 保存历史
  Future<void> _saveHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final json = jsonEncode(_chatHistory.map((s) => s.toJson()).toList());
    await prefs.setString(_historyKey, json);
  }

  /// 加载历史
  Future<void> _loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final json = prefs.getString(_historyKey);
    if (json != null) {
      final list = jsonDecode(json) as List;
      _chatHistory = list.map((s) => ChatSession.fromJson(s)).toList();
    }
  }

  /// 初始化
  Future<void> initialize() async {
    await Future.wait([_loadContext(), _loadHistory()]);
  }
}
