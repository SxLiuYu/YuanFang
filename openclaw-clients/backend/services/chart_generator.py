import logging
logger = logging.getLogger(__name__)
"""
数据可视化服务
生成图表：MPAndroidChart 配置 + Python 图表生成
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import io
import base64
from typing import Dict, List, Optional
import json

class ChartGenerator:
    """图表生成服务"""
    
    def __init__(self):
        # 中文字体配置
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    # ========== 家庭账本图表 ==========
    
    def generate_expense_pie_chart(self, stats: Dict[str, float], title: str = '月度支出分布') -> str:
        """生成支出饼图"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        labels = list(stats.keys())
        sizes = list(stats.values())
        colors = plt.cm.Set3(range(len(labels)))
        
        # 创建饼图
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.85
        )
        
        # 添加中心圆，变成甜甜圈图
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        fig.gca().add_artist(centre_circle)
        
        # 设置字体
        for text in texts:
            text.set_fontsize(12)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=16, pad=20)
        
        # 转换为 Base64
        return self._fig_to_base64(fig)
    
    def generate_trend_line_chart(self, trend_data: List[Dict], title: str = '收支趋势') -> str:
        """生成收支趋势折线图"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        months = [d['month'] for d in trend_data]
        income = [d['income'] for d in trend_data]
        expense = [d['expense'] for d in trend_data]
        balance = [d['balance'] for d in trend_data]
        
        # 绘制折线
        ax.plot(months, income, marker='o', label='收入', color='green', linewidth=2)
        ax.plot(months, expense, marker='s', label='支出', color='red', linewidth=2)
        ax.plot(months, balance, marker='^', label='结余', color='blue', linewidth=2, linestyle='--')
        
        # 设置标签
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('金额 (元)', fontsize=12)
        ax.set_title(title, fontsize=16, pad=20)
        
        # 图例
        ax.legend(loc='upper right', fontsize=10)
        
        # 网格
        ax.grid(True, alpha=0.3)
        
        # 旋转 x 轴标签
        plt.xticks(rotation=45)
        
        # 自动调整布局
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def generate_category_bar_chart(self, stats: Dict[str, float], title: str = '分类支出对比') -> str:
        """生成分类柱状图"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        categories = list(stats.keys())
        values = list(stats.values())
        
        # 创建柱状图
        bars = ax.bar(categories, values, color=plt.cm.Set2(range(len(categories))))
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'¥{height:.0f}',
                ha='center',
                va='bottom',
                fontsize=10
            )
        
        # 设置标签
        ax.set_xlabel('分类', fontsize=12)
        ax.set_ylabel('金额 (元)', fontsize=12)
        ax.set_title(title, fontsize=16, pad=20)
        
        # 旋转 x 轴标签
        plt.xticks(rotation=45)
        
        # 自动调整布局
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    # ========== 任务板图表 ==========
    
    def generate_leaderboard_chart(self, leaderboard: List[Dict]) -> str:
        """生成积分排行榜图"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        names = [entry['name'] for entry in leaderboard]
        points = [entry['points'] for entry in leaderboard]
        
        # 创建水平条形图
        bars = ax.barh(names, points, color=plt.cm.viridis(range(len(names))))
        
        # 添加数值标签
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width,
                bar.get_y() + bar.get_height()/2.,
                f'{int(width)}分',
                ha='left',
                va='center',
                fontsize=10
            )
        
        # 设置标签
        ax.set_xlabel('积分', fontsize=12)
        ax.set_title('🏆 家庭积分排行榜', fontsize=16, pad=20)
        
        # 自动调整布局
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def generate_task_status_chart(self, pending: int, completed: int, overdue: int) -> str:
        """生成任务状态图"""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        labels = ['待办', '已完成', '逾期']
        sizes = [pending, completed, overdue]
        colors = ['#FFA500', '#4CAF50', '#F44336']
        
        # 创建饼图
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90
        )
        
        # 设置字体
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(12)
            autotext.set_fontweight('bold')
        
        ax.set_title('📋 任务状态分布', fontsize=16, pad=20)
        
        return self._fig_to_base64(fig)
    
    # ========== 购物清单图表 ==========
    
    def generate_shopping_category_chart(self, items: List[Dict]) -> str:
        """生成购物分类统计图"""
        # 统计各分类数量
        category_count = {}
        for item in items:
            category = item.get('category', '其他')
            category_count[category] = category_count.get(category, 0) + 1
        
        return self.generate_category_bar_chart(category_count, '🛒 购物分类统计')
    
    def generate_price_comparison_chart(self, prices: Dict[str, Dict]) -> str:
        """生成价格对比图"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        platforms = [data['platform_name'] for data in prices.values()]
        price_values = [data['price'] for data in prices.values() if data.get('price', 0) > 0]
        
        if not price_values:
            # 无有效数据
            fig.text(0.5, 0.5, '暂无价格数据', ha='center', va='center', fontsize=16)
            return self._fig_to_base64(fig)
        
        # 创建柱状图
        bars = ax.bar(platforms, price_values, color=plt.cm.RdYlGn_r(range(len(platforms))))
        
        # 标注最低价
        min_idx = price_values.index(min(price_values))
        bars[min_idx].set_color('#4CAF50')
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'¥{height:.2f}',
                ha='center',
                va='bottom',
                fontsize=10
            )
        
        # 设置标签
        ax.set_ylabel('价格 (元)', fontsize=12)
        ax.set_title('💰 电商平台价格对比', fontsize=16, pad=20)
        
        # 旋转 x 轴标签
        plt.xticks(rotation=45)
        
        # 自动调整布局
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    # ========== 工具方法 ==========
    
    def _fig_to_base64(self, fig) -> str:
        """将图表转换为 Base64 字符串"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"
    
    def save_chart(self, chart_base64: str, filename: str):
        """保存图表到文件"""
        # 移除 data:image/png;base64, 前缀
        img_data = chart_base64.split(',')[1] if ',' in chart_base64 else chart_base64
        
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(img_data))
        
        logger.info(f"图表已保存：{filename}")


# MPAndroidChart 配置生成器（Android 使用）
class MPAndroidChartConfig:
    """MPAndroidChart 配置生成器"""
    
    @staticmethod
    def get_pie_chart_config() -> str:
        """返回饼图配置代码"""
        return """
        // 饼图配置
        pieChart.setUsePercentValues(true);
        pieChart.getDescription().setEnabled(false);
        pieChart.setExtraOffsets(5, 10, 5, 5);
        pieChart.setDragDecelerationFrictionCoef(0.95f);
        pieChart.setDrawHoleEnabled(true);
        pieChart.setHoleColor(Color.WHITE);
        pieChart.setTransparentCircleRadius(61f);
        
        // 图例配置
        Legend legend = pieChart.getLegend();
        legend.setVerticalAlignment(Legend.LegendVerticalAlignment.TOP);
        legend.setHorizontalAlignment(Legend.LegendHorizontalAlignment.RIGHT);
        legend.setOrientation(Legend.LegendOrientation.VERTICAL);
        legend.setDrawInside(false);
        """
    
    @staticmethod
    def get_line_chart_config() -> str:
        """返回折线图配置代码"""
        return """
        // 折线图配置
        lineChart.getDescription().setEnabled(false);
        lineChart.setTouchEnabled(true);
        lineChart.setDragEnabled(true);
        lineChart.setScaleEnabled(true);
        lineChart.setPinchZoom(true);
        
        // X 轴配置
        XAxis xAxis = lineChart.getXAxis();
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);
        xAxis.setGranularity(1f);
        xAxis.setGranularityEnabled(true);
        
        // Y 轴配置
        lineChart.getAxisLeft().setGranularity(100f);
        lineChart.getAxisRight().setEnabled(false);
        """
    
    @staticmethod
    def get_bar_chart_config() -> str:
        """返回柱状图配置代码"""
        return """
        // 柱状图配置
        barChart.getDescription().setEnabled(false);
        barChart.setFitBars(true);
        barChart.setDrawBarShadow(false);
        barChart.setDrawGridBackground(false);
        
        // 图例配置
        barChart.getLegend().setEnabled(true);
        barChart.getAxisRight().setEnabled(false);
        """


# 使用示例
if __name__ == '__main__':
    generator = ChartGenerator()
    
    # 生成支出饼图
    stats = {
        '餐饮': 1500,
        '交通': 500,
        '购物': 2000,
        '娱乐': 800,
        '医疗': 300
    }
    
    pie_chart = generator.generate_expense_pie_chart(stats)
    generator.save_chart(pie_chart, 'expense_pie.png')
    
    # 生成趋势图
    trend_data = [
        {'month': '10 月', 'income': 10000, 'expense': 6000, 'balance': 4000},
        {'month': '11 月', 'income': 10000, 'expense': 7000, 'balance': 3000},
        {'month': '12 月', 'income': 12000, 'expense': 8000, 'balance': 4000},
    ]
    
    trend_chart = generator.generate_trend_line_chart(trend_data)
    generator.save_chart(trend_chart, 'trend_line.png')
    
    logger.info("图表生成完成！")
