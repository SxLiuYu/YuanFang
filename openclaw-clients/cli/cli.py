#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw CLI - 手机数据接入命令行工具
让 OpenClaw 接入你的手机数据，提供智能服务

用法:
    openclaw chat "你好"                    # AI对话
    openclaw sync location --lat 39.9       # 同步位置
    openclaw sync health --steps 5000       # 同步健康
    openclaw sync payment --amount 50       # 同步支付
    openclaw report daily                   # 日报
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from commands import sync, chat, report, config
from sync.api_client import OpenClawClient

console = Console()

@click.group()
@click.version_option(version="1.0.0")
@click.option('--server', default="http://localhost:8082", help="OpenClaw服务器地址")
@click.pass_context
def cli(ctx, server):
    """OpenClaw CLI - 你的智能家庭助手
    
    支持功能:
    - AI对话
    - 位置同步与分析
    - 健康数据同步
    - 支付通知同步(自动记账)
    - 日程同步
    - 数据报告生成
    """
    ctx.ensure_object(dict)
    ctx.obj['server'] = server
    ctx.obj['client'] = OpenClawClient(server)


@cli.command()
@click.argument('message')
@click.option('--session', '-s', default=None, help="会话ID")
@click.pass_context
def chat(ctx, message, session):
    """与OpenClaw AI对话
    
    示例:
        openclaw chat "你好"
        openclaw chat "今天天气怎么样"
        openclaw chat "帮我记一笔50元餐饮支出"
    """
    client = ctx.obj['client']
    result = chat.send_message(client, message, session)
    
    if result.get('success'):
        console.print(Panel(result.get('text', ''), title="🤖 OpenClaw", border_style="blue"))
    else:
        console.print(f"[red]错误: {result.get('error', '未知错误')}[/red]")


@cli.group()
def sync():
    """数据同步命令组"""
    pass


@sync.command()
@click.option('--lat', required=True, type=float, help="纬度")
@click.option('--lng', required=True, type=float, help="经度")
@click.option('--accuracy', default=10.0, help="精度(米)")
@click.pass_context
def location(ctx, lat, lng, accuracy):
    """同步位置数据
    
    示例:
        openclaw sync location --lat 39.9042 --lng 116.4074
    """
    client = ctx.obj['client']
    result = sync.sync_location(client, lat, lng, accuracy)
    
    if result.get('success'):
        place = result.get('place_type', '未知位置')
        console.print(f"[green]✓ 位置已同步[/green]")
        console.print(f"  坐标: {lat}, {lng}")
        console.print(f"  识别为: {place}")
        
        # 触发的自动化
        automations = result.get('automations', [])
        if automations:
            console.print(f"\n[yellow]触发自动化:[/yellow]")
            for auto in automations:
                console.print(f"  • {auto}")
    else:
        console.print(f"[red]同步失败: {result.get('error')}[/red]")


@sync.command()
@click.option('--steps', type=int, help="步数")
@click.option('--heart-rate', type=int, help="心率")
@click.option('--sleep', type=float, help="睡眠时长(小时)")
@click.option('--calories', type=int, help="消耗卡路里")
@click.pass_context
def health(ctx, steps, heart_rate, sleep, calories):
    """同步健康数据
    
    示例:
        openclaw sync health --steps 5000 --sleep 7.5
        openclaw sync health --heart-rate 72
    """
    client = ctx.obj['client']
    result = sync.sync_health(client, steps, heart_rate, sleep, calories)
    
    if result.get('success'):
        console.print("[green]✓ 健康数据已同步[/green]")
        
        table = Table(title="健康数据")
        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")
        
        if steps:
            table.add_row("步数", str(steps))
        if heart_rate:
            table.add_row("心率", f"{heart_rate} bpm")
        if sleep:
            table.add_row("睡眠", f"{sleep} 小时")
        if calories:
            table.add_row("卡路里", f"{calories} kcal")
        
        console.print(table)
        
        # 健康建议
        advice = result.get('advice')
        if advice:
            console.print(f"\n[yellow]健康建议:[/yellow] {advice}")
    else:
        console.print(f"[red]同步失败: {result.get('error')}[/red]")


@sync.command()
@click.option('--amount', required=True, type=float, help="金额")
@click.option('--merchant', default="未知商户", help="商户名称")
@click.option('--category', default=None, help="分类(自动识别)")
@click.option('--type', type=click.Choice(['expense', 'income']), default='expense', help="类型")
@click.pass_context
def payment(ctx, amount, merchant, category, type):
    """同步支付数据(自动记账)
    
    示例:
        openclaw sync payment --amount 50 --merchant "美团外卖"
        openclaw sync payment --amount 5000 --type income --merchant "工资"
    """
    client = ctx.obj['client']
    result = sync.sync_payment(client, amount, merchant, category, type)
    
    if result.get('success'):
        console.print("[green]✓ 支付已记录[/green]")
        console.print(f"  金额: {amount} 元")
        console.print(f"  商户: {merchant}")
        console.print(f"  分类: {result.get('category', '自动识别')}")
        console.print(f"  类型: {'支出' if type == 'expense' else '收入'}")
        
        # 预算提醒
        budget_warning = result.get('budget_warning')
        if budget_warning:
            console.print(f"\n[yellow]⚠ 预算提醒:[/yellow] {budget_warning}")
    else:
        console.print(f"[red]记录失败: {result.get('error')}[/red]")


@sync.command()
@click.option('--title', required=True, help="事件标题")
@click.option('--date', required=True, help="日期 (YYYY-MM-DD)")
@click.option('--time', default=None, help="时间 (HH:MM)")
@click.option('--location', default=None, help="地点")
@click.pass_context
def calendar(ctx, title, date, time, location):
    """同步日程数据
    
    示例:
        openclaw sync calendar --title "开会" --date 2025-03-20 --time 10:00
    """
    client = ctx.obj['client']
    result = sync.sync_calendar(client, title, date, time, location)
    
    if result.get('success'):
        console.print("[green]✓ 日程已添加[/green]")
        console.print(f"  事件: {title}")
        console.print(f"  时间: {date} {time or ''}")
        if location:
            console.print(f"  地点: {location}")
    else:
        console.print(f"[red]添加失败: {result.get('error')}[/red]")


@cli.command()
@click.argument('type', type=click.Choice(['daily', 'weekly', 'monthly']))
@click.pass_context
def report(ctx, type):
    """生成数据报告
    
    示例:
        openclaw report daily
        openclaw report weekly
        openclaw report monthly
    """
    client = ctx.obj['client']
    result = report.generate(client, type)
    
    console.print(Panel(f"📊 {type}报告", style="bold blue"))
    
    # 健康报告
    if 'health' in result:
        health = result['health']
        console.print(f"\n[bold]健康数据[/bold]")
        console.print(f"  步数: {health.get('total_steps', 0)} 步")
        console.print(f"  平均睡眠: {health.get('avg_sleep', 0)} 小时")
        console.print(f"  活动天数: {health.get('active_days', 0)} 天")
    
    # 财务报告
    if 'finance' in result:
        finance = result['finance']
        console.print(f"\n[bold]财务数据[/bold]")
        console.print(f"  总支出: {finance.get('total_expense', 0)} 元")
        console.print(f"  总收入: {finance.get('total_income', 0)} 元")
        console.print(f"  交易次数: {finance.get('transaction_count', 0)} 笔")
        
        # 分类统计
        categories = finance.get('by_category', {})
        if categories:
            console.print(f"\n  分类明细:")
            for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
                console.print(f"    • {cat}: {amount} 元")
    
    # 位置报告
    if 'location' in result:
        location = result['location']
        console.print(f"\n[bold]位置数据[/bold]")
        console.print(f"  在家时间: {location.get('home_hours', 0)} 小时")
        console.print(f"  在公司时间: {location.get('work_hours', 0)} 小时")
        console.print(f"  外出次数: {location.get('trips', 0)} 次")


@cli.command()
@click.pass_context
def status(ctx):
    """查看系统状态"""
    client = ctx.obj['client']
    result = client.health_check()
    
    if result.get('success'):
        console.print("[green]✓ OpenClaw 服务运行正常[/green]")
        console.print(f"  服务器: {ctx.obj['server']}")
        console.print(f"  版本: {result.get('version', '1.0.0')}")
    else:
        console.print(f"[red]✗ 无法连接到 OpenClaw 服务[/red]")
        console.print(f"  请确保后端服务已启动: python backend/main.py")


@cli.command()
@click.pass_context
def interactive(ctx):
    """进入交互模式"""
    console.print(Panel("OpenClaw 交互模式", subtitle="输入 'help' 查看帮助, 'exit' 退出"))
    
    client = ctx.obj['client']
    
    while True:
        try:
            user_input = console.input("[bold cyan]你:[/bold cyan] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]再见！[/yellow]")
                break
            
            if user_input.lower() == 'help':
                console.print("""
可用命令:
  chat <消息>     - 与AI对话
  location <lat> <lng> - 同步位置
  health --steps <步数> - 同步健康
  payment <金额>  - 记录支付
  report          - 查看报告
  status          - 查看状态
  exit            - 退出
                """)
                continue
            
            # 默认当作对话
            result = chat.send_message(client, user_input)
            if result.get('success'):
                console.print(f"[bold green]OpenClaw:[/bold green] {result.get('text', '')}")
            else:
                console.print(f"[red]错误: {result.get('error')}[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]再见！[/yellow]")
            break


if __name__ == '__main__':
    cli()