import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/data_sync_service.dart';
import 'services/api_client.dart';
import 'screens/main_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // 初始化API客户端
  await OpenClawApiClient().initialize();
  
  runApp(const OpenClawApp());
}

class OpenClawApp extends StatelessWidget {
  const OpenClawApp({super.key});
  
  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => DataSyncService(),
      child: MaterialApp(
        title: 'OpenClaw',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
          useMaterial3: true,
        ),
        home: const MainScreen(),
      ),
    );
  }
}