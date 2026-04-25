import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:health/health.dart';
import 'package:permission_handler/permission_handler.dart';
import 'api_client.dart';

enum HealthDataType {
  steps,
  heartRate,
  sleep,
  activeEnergy,
  distance,
  flightsClimbed,
  oxygenSaturation,
  bloodPressure,
}

class HealthDataPoint {
  final HealthDataType type;
  final dynamic value;
  final String unit;
  final DateTime startTime;
  final DateTime endTime;
  final String? source;

  HealthDataPoint({
    required this.type,
    required this.value,
    required this.unit,
    required this.startTime,
    required this.endTime,
    this.source,
  });

  Map<String, dynamic> toJson() => {
    'type': type.name,
    'value': value,
    'unit': unit,
    'start_time': startTime.toIso8601String(),
    'end_time': endTime.toIso8601String(),
    'source': source,
  };
}

class IosHealthService extends ChangeNotifier {
  static final IosHealthService _instance = IosHealthService._internal();
  factory IosHealthService() => _instance;
  IosHealthService._internal();

  static const MethodChannel _channel = MethodChannel('com.openclaw.health');
  
  final OpenClawApiClient _apiClient = OpenClawApiClient();
  final HealthFactory _health = HealthFactory();
  
  bool _isInitialized = false;
  bool _isAuthorized = false;
  bool _isBackgroundEnabled = false;
  DateTime? _lastSyncTime;
  
  final List<HealthDataPoint> _cachedData = [];
  StreamSubscription? _backgroundSubscription;

  bool get isIosPlatform => Platform.isIOS;
  bool get isInitialized => _isInitialized;
  bool get isAuthorized => _isAuthorized;
  bool get isBackgroundEnabled => _isBackgroundEnabled;
  DateTime? get lastSyncTime => _lastSyncTime;
  List<HealthDataPoint> get cachedData => List.unmodifiable(_cachedData);

  Future<void> initialize() async {
    if (!isIosPlatform) {
      debugPrint('[IosHealthService] Not iOS platform, skipping initialization');
      return;
    }

    await _apiClient.initialize();
    
    try {
      await _channel.invokeMethod('initialize');
      _isInitialized = true;
      debugPrint('[IosHealthService] Initialized successfully');
    } on PlatformException catch (e) {
      debugPrint('[IosHealthService] Native init failed: ${e.message}');
      _isInitialized = true;
    }
    
    notifyListeners();
  }

  Future<bool> requestAuthorization() async {
    if (!isIosPlatform) {
      debugPrint('[IosHealthService] Authorization skipped: not iOS');
      return false;
    }

    final types = [
      HealthDataType.STEPS,
      HealthDataType.HEART_RATE,
      HealthDataType.SLEEP_ASLEEP,
      HealthDataType.SLEEP_IN_BED,
      HealthDataType.ACTIVE_ENERGY_BURNED,
      HealthDataType.DISTANCE_WALKING_RUNNING,
      HealthDataType.FLIGHTS_CLIMBED,
      HealthDataType.OXYGEN_SATURATION,
      HealthDataType.BLOOD_PRESSURE_SYSTOLIC,
      HealthDataType.BLOOD_PRESSURE_DIASTOLIC,
    ];

    final writeTypes = [
      HealthDataType.STEPS,
      HealthDataType.HEART_RATE,
      HealthDataType.ACTIVE_ENERGY_BURNED,
    ];

    try {
      final readGranted = await _health.requestAuthorization(types);
      if (!readGranted) {
        debugPrint('[IosHealthService] Read authorization denied');
        _isAuthorized = false;
        notifyListeners();
        return false;
      }

      final writeGranted = await _health.requestAuthorization(writeTypes);
      _isAuthorized = true;
      debugPrint('[IosHealthService] Authorization granted (read: $readGranted, write: $writeGranted)');
      
      notifyListeners();
      return true;
    } catch (e) {
      debugPrint('[IosHealthService] Authorization error: $e');
      _isAuthorized = false;
      notifyListeners();
      return false;
    }
  }

  Future<List<HealthDataPoint>> readSteps({
    DateTime? startTime,
    DateTime? endTime,
  }) async {
    if (!_checkAuthorization()) return [];

    final start = startTime ?? DateTime.now().subtract(const Duration(days: 7));
    final end = endTime ?? DateTime.now();

    try {
      final data = await _health.getHealthDataFromTypes(
        start,
        end,
        [HealthDataType.STEPS],
      );

      final points = data.map((item) => HealthDataPoint(
        type: HealthDataType.steps,
        value: item.value,
        unit: 'count',
        startTime: item.dateFrom,
        endTime: item.dateTo,
        source: item.sourceName,
      )).toList();

      _cachedData.addAll(points);
      _cleanCache();
      notifyListeners();
      return points;
    } catch (e) {
      debugPrint('[IosHealthService] Failed to read steps: $e');
      return [];
    }
  }

  Future<List<HealthDataPoint>> readHeartRate({
    DateTime? startTime,
    DateTime? endTime,
  }) async {
    if (!_checkAuthorization()) return [];

    final start = startTime ?? DateTime.now().subtract(const Duration(days: 7));
    final end = endTime ?? DateTime.now();

    try {
      final data = await _health.getHealthDataFromTypes(
        start,
        end,
        [HealthDataType.HEART_RATE],
      );

      final points = data.map((item) => HealthDataPoint(
        type: HealthDataType.heartRate,
        value: item.value,
        unit: 'bpm',
        startTime: item.dateFrom,
        endTime: item.dateTo,
        source: item.sourceName,
      )).toList();

      _cachedData.addAll(points);
      _cleanCache();
      notifyListeners();
      return points;
    } catch (e) {
      debugPrint('[IosHealthService] Failed to read heart rate: $e');
      return [];
    }
  }

  Future<List<HealthDataPoint>> readSleep({
    DateTime? startTime,
    DateTime? endTime,
  }) async {
    if (!_checkAuthorization()) return [];

    final start = startTime ?? DateTime.now().subtract(const Duration(days: 30));
    final end = endTime ?? DateTime.now();

    try {
      final asleepData = await _health.getHealthDataFromTypes(
        start,
        end,
        [HealthDataType.SLEEP_ASLEEP],
      );

      final inBedData = await _health.getHealthDataFromTypes(
        start,
        end,
        [HealthDataType.SLEEP_IN_BED],
      );

      final points = <HealthDataPoint>[];

      for (final item in asleepData) {
        points.add(HealthDataPoint(
          type: HealthDataType.sleep,
          value: item.value,
          unit: 'minutes',
          startTime: item.dateFrom,
          endTime: item.dateTo,
          source: item.sourceName,
        ));
      }

      for (final item in inBedData) {
        points.add(HealthDataPoint(
          type: HealthDataType.sleep,
          value: item.value,
          unit: 'minutes_in_bed',
          startTime: item.dateFrom,
          endTime: item.dateTo,
          source: item.sourceName,
        ));
      }

      _cachedData.addAll(points);
      _cleanCache();
      notifyListeners();
      return points;
    } catch (e) {
      debugPrint('[IosHealthService] Failed to read sleep: $e');
      return [];
    }
  }

  Future<List<HealthDataPoint>> readActiveEnergy({
    DateTime? startTime,
    DateTime? endTime,
  }) async {
    if (!_checkAuthorization()) return [];

    final start = startTime ?? DateTime.now().subtract(const Duration(days: 7));
    final end = endTime ?? DateTime.now();

    try {
      final data = await _health.getHealthDataFromTypes(
        start,
        end,
        [HealthDataType.ACTIVE_ENERGY_BURNED],
      );

      final points = data.map((item) => HealthDataPoint(
        type: HealthDataType.activeEnergy,
        value: item.value,
        unit: 'kcal',
        startTime: item.dateFrom,
        endTime: item.dateTo,
        source: item.sourceName,
      )).toList();

      _cachedData.addAll(points);
      _cleanCache();
      notifyListeners();
      return points;
    } catch (e) {
      debugPrint('[IosHealthService] Failed to read active energy: $e');
      return [];
    }
  }

  Future<int> getTodaySteps() async {
    final now = DateTime.now();
    final startOfDay = DateTime(now.year, now.month, now.day);
    
    final steps = await readSteps(startTime: startOfDay, endTime: now);
    
    int total = 0;
    for (final point in steps) {
      if (point.value is int) {
        total += point.value as int;
      } else if (point.value is double) {
        total += (point.value as double).toInt();
      }
    }
    return total;
  }

  Future<int?> getLatestHeartRate() async {
    final heartRates = await readHeartRate(
      startTime: DateTime.now().subtract(const Duration(hours: 1)),
    );
    
    if (heartRates.isEmpty) return null;
    
    heartRates.sort((a, b) => b.endTime.compareTo(a.endTime));
    final value = heartRates.first.value;
    return value is int ? value : (value as double).toInt();
  }

  Future<double> getTodaySleepHours() async {
    final now = DateTime.now();
    final startOfDay = DateTime(now.year, now.month, now.day);
    final endOfDay = startOfDay.add(const Duration(days: 1));
    
    final sleep = await readSleep(startTime: startOfDay, endTime: endOfDay);
    
    double totalMinutes = 0;
    for (final point in sleep) {
      if (point.unit == 'minutes' && point.value is num) {
        totalMinutes += (point.value as num).toDouble();
      }
    }
    return totalMinutes / 60;
  }

  Future<int> getTodayCalories() async {
    final now = DateTime.now();
    final startOfDay = DateTime(now.year, now.month, now.day);
    
    final energy = await readActiveEnergy(startTime: startOfDay, endTime: now);
    
    double total = 0;
    for (final point in energy) {
      if (point.value is num) {
        total += (point.value as num).toDouble();
      }
    }
    return total.toInt();
  }

  Future<bool> writeSteps(int steps, {DateTime? startTime, DateTime? endTime}) async {
    if (!_checkAuthorization()) return false;

    final start = startTime ?? DateTime.now().subtract(const Duration(minutes: 30));
    final end = endTime ?? DateTime.now();

    try {
      final success = await _health.writeHealthData(
        steps.toDouble(),
        HealthDataType.STEPS,
        start,
        end,
      );

      if (success) {
        debugPrint('[IosHealthService] Wrote $steps steps');
        await _syncToServer();
      }
      return success;
    } catch (e) {
      debugPrint('[IosHealthService] Failed to write steps: $e');
      return false;
    }
  }

  Future<bool> writeHeartRate(int bpm, {DateTime? timestamp}) async {
    if (!_checkAuthorization()) return false;

    final time = timestamp ?? DateTime.now();

    try {
      final success = await _health.writeHealthData(
        bpm.toDouble(),
        HealthDataType.HEART_RATE,
        time,
        time,
      );

      if (success) {
        debugPrint('[IosHealthService] Wrote heart rate: $bpm bpm');
        await _syncToServer();
      }
      return success;
    } catch (e) {
      debugPrint('[IosHealthService] Failed to write heart rate: $e');
      return false;
    }
  }

  Future<bool> writeActiveEnergy(double kcal, {DateTime? startTime, DateTime? endTime}) async {
    if (!_checkAuthorization()) return false;

    final start = startTime ?? DateTime.now().subtract(const Duration(minutes: 30));
    final end = endTime ?? DateTime.now();

    try {
      final success = await _health.writeHealthData(
        kcal,
        HealthDataType.ACTIVE_ENERGY_BURNED,
        start,
        end,
      );

      if (success) {
        debugPrint('[IosHealthService] Wrote $kcal kcal active energy');
        await _syncToServer();
      }
      return success;
    } catch (e) {
      debugPrint('[IosHealthService] Failed to write active energy: $e');
      return false;
    }
  }

  Future<void> enableBackgroundUpdates() async {
    if (!isIosPlatform || !_isAuthorized) {
      debugPrint('[IosHealthService] Cannot enable background: platform or auth issue');
      return;
    }

    try {
      await _channel.invokeMethod('enableBackgroundUpdates');
      _isBackgroundEnabled = true;
      debugPrint('[IosHealthService] Background updates enabled');
      
      _setupBackgroundListener();
      notifyListeners();
    } on PlatformException catch (e) {
      debugPrint('[IosHealthService] Failed to enable background: ${e.message}');
    }
  }

  Future<void> disableBackgroundUpdates() async {
    if (!isIosPlatform) return;

    try {
      await _channel.invokeMethod('disableBackgroundUpdates');
      _isBackgroundEnabled = false;
      await _backgroundSubscription?.cancel();
      _backgroundSubscription = null;
      debugPrint('[IosHealthService] Background updates disabled');
      notifyListeners();
    } on PlatformException catch (e) {
      debugPrint('[IosHealthService] Failed to disable background: ${e.message}');
    }
  }

  void _setupBackgroundListener() {
    _backgroundSubscription = _channel
        .receiveBroadcastStream('onHealthDataChanged')
        .listen((dynamic data) {
      debugPrint('[IosHealthService] Background data update received: $data');
      _handleBackgroundUpdate(data);
    }, onError: (dynamic error) {
      debugPrint('[IosHealthService] Background stream error: $error');
    });
  }

  Future<void> _handleBackgroundUpdate(dynamic data) async {
    await _syncToServer();
    notifyListeners();
  }

  Future<void> _syncToServer() async {
    final steps = await getTodaySteps();
    final heartRate = await getLatestHeartRate();
    final sleepHours = await getTodaySleepHours();
    final calories = await getTodayCalories();

    await _apiClient.syncHealth(
      steps: steps,
      heartRate: heartRate,
      sleepHours: sleepHours,
      calories: calories,
    );

    _lastSyncTime = DateTime.now();
    debugPrint('[IosHealthService] Synced to server at $_lastSyncTime');
  }

  Future<Map<String, dynamic>> fetchAllHealthData() async {
    final steps = await getTodaySteps();
    final heartRate = await getLatestHeartRate();
    final sleepHours = await getTodaySleepHours();
    final calories = await getTodayCalories();

    return {
      'steps': steps,
      'heart_rate': heartRate,
      'sleep_hours': sleepHours,
      'calories': calories,
      'timestamp': DateTime.now().toIso8601String(),
    };
  }

  bool _checkAuthorization() {
    if (!isIosPlatform) {
      debugPrint('[IosHealthService] Not iOS platform');
      return false;
    }
    if (!_isAuthorized) {
      debugPrint('[IosHealthService] Not authorized');
      return false;
    }
    return true;
  }

  void _cleanCache() {
    if (_cachedData.length > 1000) {
      _cachedData.removeRange(0, _cachedData.length - 1000);
    }
  }

  void clearCache() {
    _cachedData.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    _backgroundSubscription?.cancel();
    super.dispose();
  }
}