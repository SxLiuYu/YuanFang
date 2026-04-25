import 'package:flutter/services.dart';
import 'package:flutter/material.dart';
import 'package:local_auth/local_auth.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthService extends ChangeNotifier {
  final LocalAuthentication _localAuth = LocalAuthentication();
  
  bool _isLocked = true;
  bool _canCheckBiometrics = false;
  List<BiometricType> _availableBiometrics = [];
  bool _isAuthenticating = false;
  
  bool get isLocked => _isLocked;
  bool get canCheckBiometrics => _canCheckBiometrics;
  List<BiometricType> get availableBiometrics => _availableBiometrics;
  bool get isAuthenticating => _isAuthenticating;
  
  // 初始化
  Future<void> initialize() async {
    await _checkBiometrics();
    
    // 检查是否需要锁定
    final prefs = await SharedPreferences.getInstance();
    final lastActive = prefs.getInt('last_active_time');
    
    if (lastActive != null) {
      final lastActiveTime = DateTime.fromMillisecondsSinceEpoch(lastActive);
      final now = DateTime.now();
      
      // 超过30秒自动锁定
      if (now.difference(lastActiveTime).inSeconds > 30) {
        _isLocked = true;
      } else {
        _isLocked = false;
      }
    }
    
    notifyListeners();
  }
  
  // 检查生物识别支持
  Future<void> _checkBiometrics() async {
    try {
      _canCheckBiometrics = await _localAuth.canCheckBiometrics;
      _availableBiometrics = await _localAuth.getAvailableBiometrics();
    } on PlatformException catch (e) {
      debugPrint('Check biometrics error: $e');
      _canCheckBiometrics = false;
      _availableBiometrics = [];
    }
    notifyListeners();
  }
  
  // 生物识别验证
  Future<bool> authenticate() async {
    if (!_canCheckBiometrics) {
      return false;
    }
    
    _isAuthenticating = true;
    notifyListeners();
    
    try {
      final authenticated = await _localAuth.authenticate(
        localizedReason: '请验证身份以解锁应用',
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: false,
        ),
      );
      
      if (authenticated) {
        _isLocked = false;
        await _updateLastActiveTime();
      }
      
      return authenticated;
    } on PlatformException catch (e) {
      debugPrint('Authenticate error: $e');
      return false;
    } finally {
      _isAuthenticating = false;
      notifyListeners();
    }
  }
  
  // PIN码验证
  Future<bool> verifyPin(String pin) async {
    final prefs = await SharedPreferences.getInstance();
    final storedPin = prefs.getString('app_pin');
    
    if (storedPin == null) {
      // 首次设置PIN
      await prefs.setString('app_pin', pin);
      _isLocked = false;
      await _updateLastActiveTime();
      return true;
    }
    
    if (storedPin == pin) {
      _isLocked = false;
      await _updateLastActiveTime();
      return true;
    }
    
    return false;
  }
  
  // 设置PIN码
  Future<void> setPin(String pin) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('app_pin', pin);
  }
  
  // 锁定应用
  void lock() {
    _isLocked = true;
    notifyListeners();
  }
  
  // 更新最后活跃时间
  Future<void> _updateLastActiveTime() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('last_active_time', DateTime.now().millisecondsSinceEpoch);
  }
  
  // 应用进入后台时调用
  Future<void> onAppPaused() async {
    await _updateLastActiveTime();
  }
  
  // 应用恢复时调用
  Future<void> onAppResumed() async {
    final prefs = await SharedPreferences.getInstance();
    final lastActive = prefs.getInt('last_active_time');
    
    if (lastActive != null) {
      final lastActiveTime = DateTime.fromMillisecondsSinceEpoch(lastActive);
      final now = DateTime.now();
      
      // 超过30秒自动锁定
      if (now.difference(lastActiveTime).inSeconds > 30) {
        _isLocked = true;
        notifyListeners();
      }
    }
  }
  
  // 获取生物识别类型名称
  String getBiometricTypeName() {
    if (_availableBiometrics.contains(BiometricType.face)) {
      return '面容';
    } else if (_availableBiometrics.contains(BiometricType.fingerprint)) {
      return '指纹';
    } else if (_availableBiometrics.contains(BiometricType.iris)) {
      return '虹膜';
    }
    return '生物识别';
  }
}