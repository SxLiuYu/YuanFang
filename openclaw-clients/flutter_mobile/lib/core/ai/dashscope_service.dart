// AI 服务 - 通过 OpenClaw Server 统一调用
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class DashScopeService {
  static final DashScopeService _instance = DashScopeService._internal();
  factory DashScopeService() => _instance;
  DashScopeService._internal();

  late String _serverUrl;
  
  Future<void> initialize() async {
    await dotenv.load(fileName: ".env");
    _serverUrl = dotenv.env['OPENCLAW_SERVER_URL'] ?? 'https://api.openclaw.ai';
  }

  // 处理用户查询 - 通过服务端
  Future<String> processQuery(String query) async {
    try {
      final response = await http.post(
        Uri.parse('$_serverUrl/api/ai/chat'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'message': query,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return data['content'];
        } else {
          throw Exception(data['error'] ?? 'AI 服务错误');
        }
      } else {
        throw Exception('API request failed with status ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to process query: $e');
    }
  }

  // 文本生成（对话）- 通过服务端
  Future<String> generateText({
    required String prompt,
    String model = 'qwen-max',
    int maxTokens = 500,
    double temperature = 0.7,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_serverUrl/api/ai/complete'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'prompt': prompt,
          'model': model,
          'max_tokens': maxTokens,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return data['content'];
        } else {
          throw Exception(data['error'] ?? 'AI 服务错误');
        }
      } else {
        throw Exception('API request failed with status ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to generate text: $e');
    }
  }

  // 语音转文本（ASR）- 通过服务端
  Future<String> speechToText(String audioUrl) async {
    try {
      final response = await http.post(
        Uri.parse('$_serverUrl/api/voice/asr'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'audio_url': audioUrl,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return data['text'];
        } else {
          throw Exception(data['error'] ?? 'ASR 服务错误');
        }
      } else {
        throw Exception('ASR request failed with status ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to transcribe speech: $e');
    }
  }

  // 文本转语音（TTS）- 通过服务端
  Future<String> textToSpeech(String text) async {
    try {
      final response = await http.post(
        Uri.parse('$_serverUrl/api/voice/tts'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'text': text,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return data['audio_url'];
        } else {
          throw Exception(data['error'] ?? 'TTS 服务错误');
        }
      } else {
        throw Exception('TTS request failed with status ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to generate speech: $e');
    }
  }
}