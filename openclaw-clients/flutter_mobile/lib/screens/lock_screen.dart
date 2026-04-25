import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';

class LockScreen extends StatefulWidget {
  final Widget child;
  
  const LockScreen({super.key, required this.child});
  
  @override
  State<LockScreen> createState() => _LockScreenState();
}

class _LockScreenState extends State<LockScreen> with WidgetsBindingObserver {
  final _pinController = TextEditingController();
  bool _showPinInput = false;
  String _error = '';
  
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final authService = context.read<AuthService>();
      authService.initialize();
    });
  }
  
  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _pinController.dispose();
    super.dispose();
  }
  
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final authService = context.read<AuthService>();
    
    if (state == AppLifecycleState.paused) {
      authService.onAppPaused();
    } else if (state == AppLifecycleState.resumed) {
      authService.onAppResumed();
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Consumer<AuthService>(
      builder: (context, authService, child) {
        if (!authService.isLocked) {
          return widget.child;
        }
        
        return Scaffold(
          body: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Theme.of(context).primaryColor.withOpacity(0.8),
                  Theme.of(context).primaryColor.withOpacity(0.4),
                ],
              ),
            ),
            child: SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        Icons.lock_outline,
                        size: 80,
                        color: Colors.white,
                      ),
                      const SizedBox(height: 24),
                      const Text(
                        'OpenClaw',
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '验证身份以解锁',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.white70,
                        ),
                      ),
                      const SizedBox(height: 48),
                      
                      // 生物识别按钮
                      if (authService.canCheckBiometrics) ...[
                        _buildBiometricButton(authService),
                        const SizedBox(height: 24),
                        const Text(
                          '或',
                          style: TextStyle(color: Colors.white54),
                        ),
                        const SizedBox(height: 24),
                      ],
                      
                      // PIN输入
                      if (_showPinInput)
                        _buildPinInput(authService)
                      else
                        TextButton(
                          onPressed: () {
                            setState(() => _showPinInput = true);
                          },
                          child: const Text(
                            '使用PIN码',
                            style: TextStyle(color: Colors.white),
                          ),
                        ),
                      
                      if (_error.isNotEmpty) ...[
                        const SizedBox(height: 16),
                        Text(
                          _error,
                          style: const TextStyle(color: Colors.redAccent),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
  
  Widget _buildBiometricButton(AuthService authService) {
    return ElevatedButton.icon(
      onPressed: authService.isAuthenticating
          ? null
          : () async {
              final success = await authService.authenticate();
              if (!success && mounted) {
                setState(() => _error = '验证失败，请重试');
              }
            },
      icon: authService.isAuthenticating
          ? const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Colors.white,
              ),
            )
          : Icon(_getBiometricIcon(authService)),
      label: Text(
        authService.isAuthenticating
            ? '验证中...'
            : '使用${authService.getBiometricTypeName()}解锁',
      ),
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.white,
        foregroundColor: Theme.of(context).primaryColor,
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(30),
        ),
      ),
    );
  }
  
  IconData _getBiometricIcon(AuthService authService) {
    if (authService.availableBiometrics.contains(BiometricType.face)) {
      return Icons.face;
    } else if (authService.availableBiometrics.contains(BiometricType.fingerprint)) {
      return Icons.fingerprint;
    }
    return Icons.lock;
  }
  
  Widget _buildPinInput(AuthService authService) {
    return Column(
      children: [
        TextField(
          controller: _pinController,
          keyboardType: TextInputType.number,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 24,
            letterSpacing: 16,
            color: Colors.white,
          ),
          decoration: InputDecoration(
            hintText: '••••',
            hintStyle: TextStyle(color: Colors.white.withOpacity(0.3)),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: Colors.white54),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: Colors.white),
            ),
          ),
          maxLength: 4,
          obscureText: true,
          onSubmitted: (_) => _verifyPin(authService),
        ),
        const SizedBox(height: 16),
        ElevatedButton(
          onPressed: () => _verifyPin(authService),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.white,
            foregroundColor: Theme.of(context).primaryColor,
          ),
          child: const Text('验证'),
        ),
      ],
    );
  }
  
  Future<void> _verifyPin(AuthService authService) async {
    if (_pinController.text.length != 4) {
      setState(() => _error = '请输入4位PIN码');
      return;
    }
    
    final success = await authService.verifyPin(_pinController.text);
    if (!success && mounted) {
      setState(() {
        _error = 'PIN码错误';
        _pinController.clear();
      });
    }
  }
}