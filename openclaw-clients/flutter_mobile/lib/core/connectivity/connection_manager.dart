// 连接管理器 - 负责与控制端建立和维护连接
import 'dart:async';
import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:web_socket_channel/io.dart';
import 'package:http/http.dart' as http;

class ConnectionStatus {
  final bool isConnected;
  final String message;
  
  ConnectionStatus({required this.isConnected, required this.message});
}

class ConnectionManager {
  static final ConnectionManager _instance = ConnectionManager._internal();
  factory ConnectionManager() => _instance;
  ConnectionManager._internal();
  
  late IOWebSocketChannel _webSocketChannel;
  final StreamController<ConnectionStatus> _connectionStatusController = 
      StreamController<ConnectionStatus>.broadcast();
  final StreamController<String> _errorController = 
      StreamController<String>.broadcast();
  String? _controlServerUrl;
  bool _isConnected = false;
  
  Stream<ConnectionStatus> get connectionStatusStream => _connectionStatusController.stream;
  Stream<String> get onError => _errorController.stream;
  
  Future<void> initialize() async {
    await dotenv.load(fileName: ".env");
    _controlServerUrl = dotenv.env['CONTROL_SERVER_URL'];
    
    if (_controlServerUrl == null) {
      _updateConnectionStatus(false, 'Control server URL not configured');
      return;
    }
    
    _updateConnectionStatus(false, 'Ready to connect');
  }
  
  Future<void> connectToControlServer() async {
    if (_controlServerUrl == null) {
      _updateConnectionStatus(false, 'Control server URL is null');
      return;
    }
    
    try {
      _webSocketChannel = IOWebSocketChannel.connect(_controlServerUrl!);
      _webSocketChannel.stream.listen(
        (message) {
          // 处理来自控制端的消息
          _handleIncomingMessage(message);
        },
        onError: (error) {
          _errorController.add('Connection error: $error');
          _updateConnectionStatus(false, 'Connection error: $error');
        },
        onDone: () {
          _updateConnectionStatus(false, 'Connection closed');
          _isConnected = false;
        },
      );
      
      _isConnected = true;
      _updateConnectionStatus(true, 'Connected to control server');
    } catch (e) {
      _errorController.add('Failed to connect: $e');
      _updateConnectionStatus(false, 'Failed to connect: $e');
    }
  }
  
  void sendMessage(dynamic message) {
    if (_isConnected) {
      try {
        _webSocketChannel.sink.add(jsonEncode(message));
      } catch (e) {
        _errorController.add('Failed to send message: $e');
      }
    } else {
      _errorController.add('Not connected to control server');
    }
  }
  
  void _handleIncomingMessage(dynamic message) {
    // 处理控制端指令
    // 例如：请求特定数据、调整收集频率等
    try {
      final decodedMessage = jsonDecode(message as String);
      // TODO: 实现具体的消息处理逻辑
    } catch (e) {
      _errorController.add('Failed to parse incoming message: $e');
    }
  }
  
  void _updateConnectionStatus(bool connected, String message) {
    _connectionStatusController.add(ConnectionStatus(
      isConnected: connected,
      message: message,
    ));
  }
  
  void dispose() {
    _webSocketChannel.sink.close();
    _connectionStatusController.close();
    _errorController.close();
  }
}