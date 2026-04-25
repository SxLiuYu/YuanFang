// 语音识别服务 - 集成Flutter语音识别和DashScope API
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:openclaw_home_assistant/core/ai/dashscope_service.dart';

class VoiceRecognitionResult {
  final String recognizedText;
  final double confidence;
  final bool isFinal;
  
  VoiceRecognitionResult({
    required this.recognizedText,
    required this.confidence,
    required this.isFinal,
  });
}

class VoiceService {
  static final VoiceService _instance = VoiceService._internal();
  factory VoiceService() => _instance;
  VoiceService._internal();
  
  final stt.SpeechToText _speech = stt.SpeechToText();
  final StreamController<String> _resultController = 
      StreamController<String>.broadcast();
  late SharedPreferences _prefs;
  
  Stream<String> get onResult => _resultController.stream;
  Stream<String> get onError => _errorController.stream;
  final StreamController<String> _errorController = StreamController<String>.broadcast();
  
  Future<void> initialize() async {
    _prefs = await SharedPreferences.getInstance();
    await _speech.initialize(
      onError: _handleError,
      onStatus: _handleStatus,
    );
  }
  
  Future<bool> startListening() async {
    if (!_speech.isAvailable) {
      _errorController.add('Speech recognition not available');
      return false;
    }
    
    try {
      await _speech.listen(
        onResult: _handleResult,
        localeId: 'zh_CN', // 中文识别
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 2),
        partialResults: true,
        onSoundLevelChange: _handleSoundLevel,
      );
      return true;
    } catch (e) {
      _errorController.add('Failed to start listening: $e');
      return false;
    }
  }
  
  void stopListening() {
    _speech.stop();
  }
  
  void cancelListening() {
    _speech.cancel();
  }
  
  // 处理语音识别结果
  void _handleResult(stt.SpeechRecognitionResult result) {
    if (result.isFinal && result.confidence > 0.7) {
      _resultController.add(result.recognizedWords);
    }
  }
  
  void _handleError(stt.SpeechRecognitionError error) {
    _errorController.add(error.errorMsg);
  }
  
  void _handleStatus(String status) {
    debugPrint('Speech recognition status: $status');
  }
  
  void _handleSoundLevel(double level) {
    // 可用于UI反馈，显示音量级别
  }
  
  bool get isListening => _speech.isListening;
  bool get isAvailable => _speech.isAvailable;
}