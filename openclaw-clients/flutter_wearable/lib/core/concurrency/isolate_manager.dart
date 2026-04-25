// Flutter手表端并发管理 - 轻量级Isolate Manager
// 针对Wear OS/WatchOS的资源限制优化
import 'dart:async';
import 'dart:isolate';

class WearableIsolateManager {
  static final WearableIsolateManager _instance = WearableIsolateManager._internal();
  factory WearableIsolateManager() => _instance;
  WearableIsolateManager._internal();

  final Map<String, Isolate> _isolates = {};
  final Map<String, SendPort> _sendPorts = {};

  /// 启动轻量级Isolate（手表端资源有限，限制并发数）
  Future<void> spawnLightweightIsolate(String name, String entryPoint, dynamic args) async {
    // 手表端限制同时运行的Isolate数量
    if (_isolates.length >= 2) {
      throw Exception('Wearable device resource limit: max 2 isolates allowed');
    }
    
    final receivePort = ReceivePort();
    final isolate = await Isolate.spawn(
      _isolateEntryPoint,
      {
        'entryPoint': entryPoint,
        'args': args,
        'sendPort': receivePort.sendPort,
      },
      debugName: name,
      // 手表端优化：减少内存占用
      paused: false,
    );
    
    _isolates[name] = isolate;
    
    receivePort.listen((message) {
      if (message is Map && message['type'] == 'sendPort') {
        _sendPorts[name] = message['port'] as SendPort;
      }
    });
  }

  /// 发送消息到Isolate
  void sendMessageToIsolate(String name, dynamic message) {
    final sendPort = _sendPorts[name];
    if (sendPort != null) {
      sendPort.send(message);
    }
  }

  /// 终止Isolate并释放资源
  void killIsolate(String name) {
    final isolate = _isolates[name];
    if (isolate != null) {
      isolate.kill(priority: Isolate.immediate);
      _isolates.remove(name);
      _sendPorts.remove(name);
    }
  }

  /// 终止所有Isolate（手表端低电量时调用）
  void killAllIsolates() {
    for (final isolate in _isolates.values) {
      isolate.kill(priority: Isolate.immediate);
    }
    _isolates.clear();
    _sendPorts.clear();
  }

  static void _isolateEntryPoint(dynamic args) {
    final entryPoint = args['entryPoint'] as String;
    final messageArgs = args['args'];
    final replyTo = args['sendPort'] as SendPort;

    final entryPoints = {
      'healthDataSync': _handleHealthDataSync,
      'quickCommand': _handleQuickCommand,
      'notificationProcess': _handleNotificationProcess,
    };

    if (entryPoints.containsKey(entryPoint)) {
      final responsePort = ReceivePort();
      replyTo.send({
        'type': 'sendPort',
        'port': responsePort.sendPort,
      });

      responsePort.listen((message) {
        entryPoints[entryPoint]!(message, replyTo);
      });
    }
  }

  // 手表端专用处理函数
  static void _handleHealthDataSync(dynamic healthData, SendPort replyTo) {
    // 处理健康数据同步（心率、步数等）
    // 模拟轻量级处理
    replyTo.send({
      'type': 'healthDataSynced',
      'status': 'success',
    });
  }

  static void _handleQuickCommand(dynamic command, SendPort replyTo) {
    // 处理快速命令（开关灯、调节温度等）
    replyTo.send({
      'type': 'quickCommandExecuted',
      'command': command,
      'status': 'success',
    });
  }

  static void _handleNotificationProcess(dynamic notification, SendPort replyTo) {
    // 处理通知（简化内容以适应手表屏幕）
    replyTo.send({
      'type': 'notificationProcessed',
      'summary': 'Notification processed for wearable',
    });
  }
}