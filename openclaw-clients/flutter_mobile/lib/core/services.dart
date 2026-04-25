// 核心服务初始化和管理
import 'package:openclaw_home_assistant/core/voice/voice_service.dart';
import 'package:openclaw_home_assistant/core/ai/dashscope_service.dart';
import 'package:openclaw_home_assistant/core/connectivity/connection_manager.dart';
import 'package:openclaw_home_assistant/core/data_collection/data_collector.dart';

class CoreServices {
  static final CoreServices _instance = CoreServices._internal();
  factory CoreServices() => _instance;
  CoreServices._internal();

  late final VoiceService voiceService;
  late final DashScopeService dashScopeService;
  late final ConnectionManager connectionManager;
  late final DataCollector dataCollector;

  Future<void> initialize() async {
    // 初始化连接管理器
    connectionManager = ConnectionManager();
    await connectionManager.initialize();

    // 初始化数据收集器
    dataCollector = DataCollector();
    await dataCollector.initialize();

    // 初始化语音服务
    voiceService = VoiceService();
    await voiceService.initialize();

    // 初始化DashScope AI服务
    dashScopeService = DashScopeService();
    await dashScopeService.initialize();
  }

  Future<void> startAllServices() async {
    // 启动连接
    await connectionManager.connectToControlServer();
    
    // 启动数据收集
    await dataCollector.startAllCollections();
    
    // 启动语音监听（按需启动）
    // await voiceService.startListening();
  }
}