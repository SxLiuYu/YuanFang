import 'package:flutter/material.dart';
import 'api_client.dart';

enum DeviceType { light, airConditioner, curtain, speaker, unknown }

class SmartDevice {
  final String deviceId;
  final String name;
  final DeviceType type;
  final String room;
  final bool isOnline;
  final Map<String, dynamic> status;
  
  SmartDevice({
    required this.deviceId,
    required this.name,
    required this.type,
    required this.room,
    this.isOnline = true,
    this.status = const {},
  });
  
  factory SmartDevice.fromJson(Map<String, dynamic> json) {
    return SmartDevice(
      deviceId: json['device_id'] ?? '',
      name: json['name'] ?? '',
      type: _parseType(json['type']),
      room: json['room'] ?? '',
      isOnline: json['is_online'] ?? true,
      status: Map<String, dynamic>.from(json['status'] ?? {}),
    );
  }
  
  static DeviceType _parseType(String? type) {
    switch (type) {
      case 'light': return DeviceType.light;
      case 'air_conditioner': return DeviceType.airConditioner;
      case 'curtain': return DeviceType.curtain;
      case 'speaker': return DeviceType.speaker;
      default: return DeviceType.unknown;
    }
  }
}

class SmartHomeService extends ChangeNotifier {
  final OpenClawApiClient _apiClient = OpenClawApiClient();
  
  List<SmartDevice> _devices = [];
  bool _isLoading = false;
  
  List<SmartDevice> get devices => _devices;
  bool get isLoading => _isLoading;
  
  // 发现设备
  Future<void> discoverDevices() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final response = await _apiClient.get('/api/v1/home/devices', {});
      
      if (response['success'] == true) {
        final data = response['data'] as List;
        _devices = data.map((json) => SmartDevice.fromJson(json)).toList();
      }
    } catch (e) {
      debugPrint('Discover devices error: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // 控制设备
  Future<bool> controlDevice(String deviceId, String action, {dynamic value}) async {
    try {
      final response = await _apiClient.post(
        '/api/v1/home/devices/$deviceId/control',
        {'action': action, 'value': value},
      );
      
      return response['success'] == true;
    } catch (e) {
      debugPrint('Control device error: $e');
      return false;
    }
  }
  
  // 获取设备状态
  Future<Map<String, dynamic>?> getDeviceStatus(String deviceId) async {
    try {
      final response = await _apiClient.get(
        '/api/v1/home/devices/$deviceId/status',
        {},
      );
      
      if (response['success'] == true) {
        return response['data'];
      }
      return null;
    } catch (e) {
      debugPrint('Get device status error: $e');
      return null;
    }
  }
  
  // 便捷方法：开灯
  Future<bool> turnOnLight(String deviceId) => controlDevice(deviceId, 'turn_on');
  
  // 关灯
  Future<bool> turnOffLight(String deviceId) => controlDevice(deviceId, 'turn_off');
  
  // 设置亮度
  Future<bool> setBrightness(String deviceId, int brightness) =>
      controlDevice(deviceId, 'set_brightness', value: brightness);
  
  // 设置空调温度
  Future<bool> setTemperature(String deviceId, int temperature) =>
      controlDevice(deviceId, 'set_temperature', value: temperature);
  
  // 打开窗帘
  Future<bool> openCurtain(String deviceId) => controlDevice(deviceId, 'open');
  
  // 关闭窗帘
  Future<bool> closeCurtain(String deviceId) => controlDevice(deviceId, 'close');
  
  // 播放音乐
  Future<bool> play(String deviceId) => controlDevice(deviceId, 'play');
  
  // 暂停
  Future<bool> pause(String deviceId) => controlDevice(deviceId, 'pause');
  
  // 设置音量
  Future<bool> setVolume(String deviceId, int volume) =>
      controlDevice(deviceId, 'set_volume', value: volume);
}