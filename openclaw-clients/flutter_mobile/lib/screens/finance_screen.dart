import 'package:flutter/material.dart';

class FinanceScreen extends StatefulWidget {
  const FinanceScreen({super.key});
  
  @override
  State<FinanceScreen> createState() => _FinanceScreenState();
}

class _FinanceScreenState extends State<FinanceScreen> {
  final _amountController = TextEditingController();
  final _merchantController = TextEditingController();
  final _categoryController = TextEditingController();
  
  @override
  void dispose() {
    _amountController.dispose();
    _merchantController.dispose();
    _categoryController.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('财务管理'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 本月概览
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  const Text('本月概览', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildSummaryItem('支出', '¥1,250', Colors.red),
                      _buildSummaryItem('收入', '¥5,000', Colors.green),
                      _buildSummaryItem('结余', '¥3,750', Colors.blue),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          
          // 快速记账
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('快速记账', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _amountController,
                    decoration: const InputDecoration(
                      labelText: '金额',
                      prefixText: '¥',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _merchantController,
                    decoration: const InputDecoration(
                      labelText: '商户/描述',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _categoryController,
                    decoration: const InputDecoration(
                      labelText: '分类（可选）',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () => _recordPayment('expense'),
                          icon: const Icon(Icons.remove),
                          label: const Text('支出'),
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () => _recordPayment('income'),
                          icon: const Icon(Icons.add),
                          label: const Text('收入'),
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          
          // 最近记录
          Card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Padding(
                  padding: EdgeInsets.all(16),
                  child: Text('最近记录', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const CircleAvatar(
                    backgroundColor: Colors.red,
                    child: Icon(Icons.restaurant, color: Colors.white),
                  ),
                  title: const Text('美团外卖'),
                  subtitle: const Text('今天 12:30'),
                  trailing: const Text('-¥35', style: TextStyle(color: Colors.red)),
                ),
                ListTile(
                  leading: const CircleAvatar(
                    backgroundColor: Colors.red,
                    child: Icon(Icons.directions_car, color: Colors.white),
                  ),
                  title: const Text('滴滴出行'),
                  subtitle: const Text('今天 08:15'),
                  trailing: const Text('-¥25', style: TextStyle(color: Colors.red)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildSummaryItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: TextStyle(color: Colors.grey[600])),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color),
        ),
      ],
    );
  }
  
  void _recordPayment(String type) {
    if (_amountController.text.isEmpty || _merchantController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请填写金额和商户')),
      );
      return;
    }
    
    // TODO: 调用API同步
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('${type == 'expense' ? '支出' : '收入'}已记录')),
    );
    
    _amountController.clear();
    _merchantController.clear();
    _categoryController.clear();
  }
}