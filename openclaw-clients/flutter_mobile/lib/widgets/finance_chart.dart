import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

class ExpensePieChart extends StatelessWidget {
  final List<ExpenseCategory> categories;

  const ExpensePieChart({
    super.key,
    required this.categories,
  });

  @override
  Widget build(BuildContext context) {
    final total = categories.fold(0.0, (sum, cat) => sum + cat.amount);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '支出分类',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              Text(
                '总计: ¥${total.toStringAsFixed(2)}',
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                flex: 3,
                child: SizedBox(
                  height: 180,
                  child: PieChart(
                    PieChartData(
                      sectionsSpace: 2,
                      centerSpaceRadius: 40,
                      sections: _buildPieSections(total),
                      pieTouchData: PieTouchData(
                        touchCallback: (FlTouchEvent event, pieTouchResponse) {},
                      ),
                    ),
                  ),
                ),
              ),
              Expanded(
                flex: 2,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: categories.take(4).map((cat) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: _buildLegendItem(
                        cat.icon,
                        cat.name,
                        cat.color,
                        '¥${cat.amount.toStringAsFixed(0)}',
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  List<PieChartSectionData> _buildPieSections(double total) {
    return categories.asMap().entries.map((entry) {
      final cat = entry.value;
      final percentage = (cat.amount / total * 100);
      return PieChartSectionData(
        color: cat.color,
        value: cat.amount,
        title: '${percentage.toStringAsFixed(1)}%',
        radius: 50,
        titleStyle: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
        titlePositionPercentageOffset: 0.55,
      );
    }).toList();
  }

  Widget _buildLegendItem(IconData icon, String label, Color color, String amount) {
    return Row(
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
              ),
              Text(
                amount,
                style: const TextStyle(fontSize: 10, color: Colors.grey),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class MonthlyTrendChart extends StatelessWidget {
  final List<MonthlyData> monthlyData;
  final double? budget;

  const MonthlyTrendChart({
    super.key,
    required this.monthlyData,
    this.budget,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 220,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '月度趋势',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              Row(
                children: [
                  _buildIndicator('收入', Colors.green),
                  const SizedBox(width: 12),
                  _buildIndicator('支出', Colors.red),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  getDrawingHorizontalLine: (value) {
                    return FlLine(
                      color: Colors.grey.withOpacity(0.2),
                      strokeWidth: 1,
                    );
                  },
                ),
                titlesData: FlTitlesData(
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 50,
                      getTitlesWidget: (value, meta) {
                        return Text(
                          '¥${(value / 1000).toStringAsFixed(0)}k',
                          style: const TextStyle(fontSize: 10, color: Colors.grey),
                        );
                      },
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 30,
                      getTitlesWidget: (value, meta) {
                        final months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
                        if (value.toInt() < months.length) {
                          return Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: Text(
                              months[value.toInt()],
                              style: const TextStyle(fontSize: 10, color: Colors.grey),
                            ),
                          );
                        }
                        return const Text('');
                      },
                    ),
                  ),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                borderData: FlBorderData(show: false),
                minX: 0,
                maxX: (monthlyData.length - 1).toDouble(),
                minY: 0,
                maxY: _calculateMaxY() * 1.2,
                lineBarsData: [
                  _buildLine(
                    monthlyData.map((d) => d.income).toList(),
                    Colors.green,
                    true,
                  ),
                  _buildLine(
                    monthlyData.map((d) => d.expense).toList(),
                    Colors.red,
                    false,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  double _calculateMaxY() {
    final allValues = [
      ...monthlyData.map((d) => d.income),
      ...monthlyData.map((d) => d.expense),
    ];
    return allValues.reduce((a, b) => a > b ? a : b);
  }

  LineChartBarData _buildLine(List<double> values, Color color, bool showDots) {
    final spots = values.asMap().entries.map((e) {
      return FlSpot(e.key.toDouble(), e.value);
    }).toList();

    return LineChartBarData(
      spots: spots,
      isCurved: true,
      color: color,
      barWidth: 2,
      isStrokeCapRound: true,
      dotData: FlDotData(
        show: showDots,
        getDotPainter: (spot, percent, barData, index) {
          return FlDotCirclePainter(
            radius: 3,
            color: color,
            strokeWidth: 0,
          );
        },
      ),
      belowBarData: BarAreaData(
        show: true,
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            color.withOpacity(0.2),
            color.withOpacity(0.02),
          ],
        ),
      ),
    );
  }

  Widget _buildIndicator(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: Colors.grey),
        ),
      ],
    );
  }
}

class BudgetProgressBar extends StatelessWidget {
  final String category;
  final double budget;
  final double spent;
  final IconData icon;
  final Color color;

  const BudgetProgressBar({
    super.key,
    required this.category,
    required this.budget,
    required this.spent,
    required this.icon,
    required this.color,
  });

  double get percentage => (spent / budget).clamp(0.0, 1.0);
  bool get isOverBudget => spent > budget;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, size: 20, color: color),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          category,
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                        Text(
                          '¥${spent.toStringAsFixed(0)} / ¥${budget.toStringAsFixed(0)}',
                          style: TextStyle(
                            fontSize: 12,
                            color: isOverBudget ? Colors.red : Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      isOverBudget
                          ? '已超支 ¥${(spent - budget).toStringAsFixed(0)}'
                          : '剩余 ¥${(budget - spent).toStringAsFixed(0)}',
                      style: TextStyle(
                        fontSize: 11,
                        color: isOverBudget ? Colors.red : Colors.green,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Stack(
              children: [
                Container(
                  height: 8,
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                FractionallySizedBox(
                  widthFactor: percentage,
                  child: Container(
                    height: 8,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: isOverBudget
                            ? [Colors.red[400]!, Colors.red[600]!]
                            : [color.withOpacity(0.7), color],
                      ),
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Text(
                '${(percentage * 100).toStringAsFixed(0)}%',
                style: TextStyle(
                  fontSize: 10,
                  color: isOverBudget ? Colors.red : color,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class BudgetOverviewCard extends StatelessWidget {
  final double totalBudget;
  final double totalSpent;
  final List<BudgetProgressBar> budgetItems;

  const BudgetOverviewCard({
    super.key,
    required this.totalBudget,
    required this.totalSpent,
    required this.budgetItems,
  });

  @override
  Widget build(BuildContext context) {
    final percentage = (totalSpent / totalBudget).clamp(0.0, 1.0);
    final isOverBudget = totalSpent > totalBudget;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '预算总览',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: isOverBudget ? Colors.red[50] : Colors.green[50],
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  isOverBudget ? '超支' : '正常',
                  style: TextStyle(
                    color: isOverBudget ? Colors.red : Colors.green,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildSummaryItem(
                '总预算',
                '¥${totalBudget.toStringAsFixed(0)}',
                Colors.blue,
              ),
              _buildSummaryItem(
                '已花费',
                '¥${totalSpent.toStringAsFixed(0)}',
                isOverBudget ? Colors.red : Colors.orange,
              ),
              _buildSummaryItem(
                '剩余',
                '¥${(totalBudget - totalSpent).abs().toStringAsFixed(0)}',
                isOverBudget ? Colors.red : Colors.green,
              ),
            ],
          ),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: percentage,
              backgroundColor: Colors.grey[200],
              valueColor: AlwaysStoppedAnimation<Color>(
                isOverBudget ? Colors.red : Colors.blue,
              ),
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 16),
          ...budgetItems,
        ],
      ),
    );
  }

  Widget _buildSummaryItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 11,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }
}

class ExpenseCategory {
  final String name;
  final double amount;
  final Color color;
  final IconData icon;

  ExpenseCategory({
    required this.name,
    required this.amount,
    required this.color,
    required this.icon,
  });
}

class MonthlyData {
  final int month;
  final double income;
  final double expense;

  MonthlyData({
    required this.month,
    required this.income,
    required this.expense,
  });
}

class FinanceDashboard extends StatelessWidget {
  final List<ExpenseCategory> categories;
  final List<MonthlyData> monthlyData;
  final List<BudgetProgressBar> budgetItems;
  final double totalBudget;
  final double totalSpent;

  const FinanceDashboard({
    super.key,
    required this.categories,
    required this.monthlyData,
    required this.budgetItems,
    required this.totalBudget,
    required this.totalSpent,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          ExpensePieChart(categories: categories),
          const SizedBox(height: 16),
          MonthlyTrendChart(monthlyData: monthlyData),
          const SizedBox(height: 16),
          BudgetOverviewCard(
            totalBudget: totalBudget,
            totalSpent: totalSpent,
            budgetItems: budgetItems,
          ),
        ],
      ),
    );
  }
}