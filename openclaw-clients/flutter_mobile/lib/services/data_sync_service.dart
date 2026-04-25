import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:location/location.dart';
import 'package:health/health.dart';
import 'package:permission_handler/permission_handler.dart';
import 'api_client.dart';

enum PlaceType { home, work, other }

class LocationData {
  final double latitude;
  final double longitude;
  final double accuracy;
  final PlaceType placeType;
  final DateTime timestamp;
  
  LocationData({
    required this.latitude,
    required this.longitude,
    this.accuracy = 10.0,
    this.placeType = PlaceType.other,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
  
  String get placeTypeString {
    switch (placeType) {
      case PlaceType.home: return '家';
      case PlaceType.work: return '公司';
      case PlaceType.other: return '其他';
    }
  }
}

class HealthData {
  final int? steps;
  final int? heartRate;
  final double? sleepHours;
  final int? calories;
  final DateTime timestamp;
  
  HealthData({
    this.steps,
    this.heartRate,
    this.sleepHours,
    this.calories,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

class DataSyncService extends ChangeNotifier {
  static final DataSyncService _instance = DataSyncService._internal();
  factory DataSyncService() => _instance;
  DataSyncService._internal();
  
  final OpenClawApiClient _apiClient = OpenClawApiClient();
  
  // 位置服务
  final Location _location = Location();
  StreamSubscription<LocationData>? _locationSubscription;
  
  // 健康服务
  final HealthFactory _health = HealthFactory();
  
  // 已知地点
  final Map<String, List<double>> _knownPlaces = {
    'home': [39.9042, 116.4074],
    'work': [39.9142, 116.4174],
  };
  
  // 数据缓存
  final List<LocationData> _locationHistory = [];
  final List<HealthData> _healthHistory = [];
  
  // 同步状态
  bool _isSyncing = false;
  DateTime? _lastSyncTime;
  
  bool get isSyncing => _isSyncing;
  DateTime? get lastSyncTime => _lastSyncTime;
  List<LocationData> get locationHistory => _locationHistory;
  List<HealthData> get healthHistory => _healthHistory;
  
  // ========== 初始化 ==========
  
  Future<void> initialize() async {
    await _apiClient.initialize();
    await _requestPermissions();
  }
  
  Future<void> _requestPermissions() async {
    // 位置权限
    final locationStatus = await Permission.location.request();
    if (!locationStatus.isGranted) {
      debugPrint('Location permission denied');
    }
    
    // 健康权限
    final healthStatus = await Permission.activityRecognition.request();
    if (!healthStatus.isGranted) {
      debugPrint('Health permission denied');
    }
  }
  
  // ========== 位置采集 ==========
  
  Future<void> startLocationTracking() async {
    bool _serviceEnabled;
    PermissionStatus _permissionGranted;
    
    _serviceEnabled = await _location.serviceEnabled();
    if (!_serviceEnabled) {
      _serviceEnabled = await _location.requestService();
      if (!_serviceEnabled) return;
    }
    
    _permissionGranted = await _location.hasPermission();
    if (_permissionGranted == PermissionStatus.denied) {
      _permissionGranted = await _location.requestPermission();
      if (_permissionGranted != PermissionStatus.granted) return;
    }
    
    _locationSubscription = _location.onLocationChanged.listen(
      (LocationData currentLocation) async {
        await _handleLocationUpdate(currentLocation);
      },
    );
  }
  
  Future<void> stopLocationTracking() async {
    await _locationSubscription?.cancel();
    _locationSubscription = null;
  }
  
  Future<void> _handleLocationUpdate(LocationData location) async {
    final placeType = _detectPlaceType(location.latitude!, location.longitude!);
    
    final locationData = LocationData(
      latitude: location.latitude!,
      longitude: location.longitude!,
      accuracy: location.accuracy!,
      placeType: placeType,
    );
    
    _locationHistory.add(locationData);
    
    // 同步到服务器
    await _apiClient.syncLocation(
      latitude: locationData.latitude,
      longitude: locationData.longitude,
      accuracy: locationData.accuracy,
    );
    
    notifyListeners();
  }
  
  PlaceType _detectPlaceType(double lat, double lng) {
    for (final entry in _knownPlaces.entries) {
      final placeCoords = entry.value;
      final distance = _calculateDistance(lat, lng, placeCoords[0], placeCoords[1]);
      
      if (distance < 100) {
        return entry.key == 'home' ? PlaceType.home : PlaceType.work;
      }
    }
    return PlaceType.other;
  }
  
  double _calculateDistance(double lat1, double lng1, double lat2, double lng2) {
    const double R = 6371000;
    final double phi1 = lat1 * pi / 180;
    final double phi2 = lat2 * pi / 180;
    final double deltaPhi = (lat2 - lat1) * pi / 180;
    final double deltaLambda = (lng2 - lng1) * pi / 180;
    
    final double a = sin(deltaPhi / 2) * sin(deltaPhi / 2) +
        cos(phi1) * cos(phi2) * sin(deltaLambda / 2) * sin(deltaLambda / 2);
    final double c = 2 * atan2(sqrt(a), sqrt(1 - a));
    
    return R * c;
  }
  
  // ========== 健康数据采集 ==========
  
  Future<HealthData?> fetchHealthData() async {
    final types = [
      HealthDataType.STEPS,
      HealthDataType.HEART_RATE,
      HealthDataType.SLEEP_ASLEEP,
      HealthDataType.ACTIVE_ENERGY_BURNED,
    ];
    
    final now = DateTime.now();
    final startOfDay = DateTime(now.year, now.month, now.day);
    
    try {
      final accessGranted = await _health.requestAuthorization(types);
      if (!accessGranted) {
        debugPrint('Health authorization denied');
        return null;
      }
      
      int? steps;
      int? heartRate;
      double? sleepHours;
      int? calories;
      
      // 获取步数
      final stepsData = await _health.getHealthDataFromTypes(
        startOfDay,
        now,
        [HealthDataType.STEPS],
      );
      if (stepsData.isNotEmpty) {
        steps = stepsData.fold(0, (sum, item) => sum + (item.value as int));
      }
      
      // 获取心率
      final heartRateData = await _health.getHealthDataFromTypes(
        startOfDay,
        now,
        [HealthDataType.HEART_RATE],
      );
      if (heartRateData.isNotEmpty) {
        heartRate = heartRateData.last.value as int;
      }
      
      // 获取睡眠
      final sleepData = await _health.getHealthDataFromTypes(
        startOfDay,
        now,
        [HealthDataType.SLEEP_ASLEEP],
      );
      if (sleepData.isNotEmpty) {
        final sleepMinutes = sleepData.fold(0, (sum, item) => sum + (item.value as int));
        sleepHours = sleepMinutes / 60;
      }
      
      // 获取卡路里
      final caloriesData = await _health.getHealthDataFromTypes(
        startOfDay,
        now,
        [HealthDataType.ACTIVE_ENERGY_BURNED],
      );
      if (caloriesData.isNotEmpty) {
        calories = caloriesData.fold(0, (sum, item) => sum + (item.value as int)).toInt();
      }
      
      final healthData = HealthData(
        steps: steps,
        heartRate: heartRate,
        sleepHours: sleepHours,
        calories: calories,
      );
      
      _healthHistory.add(healthData);
      
      // 同步到服务器
      await _apiClient.syncHealth(
        steps: steps,
        heartRate: heartRate,
        sleepHours: sleepHours,
        calories: calories,
      );
      
      notifyListeners();
      return healthData;
      
    } catch (e) {
      debugPrint('Failed to fetch health data: $e');
      return null;
    }
  }
  
  // ========== 后台同步 ==========
  
  Future<void> startBackgroundSync({Duration interval = const Duration(minutes: 5)}) async {
    Timer.periodic(interval, (timer) async {
      await syncAllData();
    });
  }
  
  Future<void> syncAllData() async {
    if (_isSyncing) return;
    
    _isSyncing = true;
    notifyListeners();
    
    try {
      // 同步健康数据
      await fetchHealthData();
      
      _lastSyncTime = DateTime.now();
    } finally {
      _isSyncing = false;
      notifyListeners();
    }
  }
}