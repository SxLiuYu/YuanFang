// Flutter移动端原生桥接 - 用于性能关键模块
import 'dart:async';
import 'package:flutter/services.dart';

class NativeBridge {
  static const _channel = MethodChannel('com.openclaw.homeassistant/native');

  /// 调用原生语音识别
  Future<String?> recognizeSpeech() async {
    try {
      final result = await _channel.invokeMethod('recognizeSpeech');
      return result as String?;
    } on PlatformException catch (e) {
      print('语音识别失败: ${e.message}');
      return null;
    }
  }

  /// 调用原生TTS
  Future<void> speakText(String text) async {
    try {
      await _channel.invokeMethod('speakText', {'text': text});
    } on PlatformException catch (e) {
      print('TTS播放失败: ${e.message}');
    }
  }

  /// 启动原生后台服务
  Future<bool> startBackgroundService() async {
    try {
      final result = await _channel.invokeMethod('startBackgroundService');
      return result as bool;
    } on PlatformException catch (e) {
      print('启动后台服务失败: ${e.message}');
      return false;
    }
  }

  /// 停止原生后台服务
  Future<void> stopBackgroundService() async {
    try {
      await _channel.invokeMethod('stopBackgroundService');
    } on PlatformException catch (e) {
      print('停止后台服务失败: ${e.message}');
    }
  }

  /// 获取设备传感器数据
  Future<Map<String, dynamic>?> getSensorData() async {
    try {
      final result = await _channel.invokeMethod('getSensorData');
      return result as Map<String, dynamic>?;
    } on PlatformException catch (e) {
      print('获取传感器数据失败: ${e.message}');
      return null;
    }
  }
}