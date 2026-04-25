import 'package:flutter/material.dart';

class LocationScreen extends StatelessWidget {
  const LocationScreen({super.key});
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('位置记录'),
      ),
      body: const Center(
        child: Text('位置地图（待实现）'),
      ),
    );
  }
}