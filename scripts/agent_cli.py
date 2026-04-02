"""
龙虾军团 Agent CLI
Usage: python agent_cli.py "你的任务"
"""
import sys
import json
from agents import LobsterArmyCrew


def main():
    if len(sys.argv) < 2:
        print("用法: python agent_cli.py <任务描述>")
        print("示例: python agent_cli.py '帮我查一下今天的天气'")
        print("       python agent_cli.py '分析一下我是否在家'")
        print("       python agent_cli.py '研究一�?DeepSeek V3 的特�?")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    
    print(f"\n🦞 龙虾军团启动...")
    print(f"📋 任务: {task}\n")
    
    crew = LobsterArmyCrew()
    result = crew.run(task)
    
    print("\n" + "=" * 50)
    print("📊 最终结�?")
    print("=" * 50)
    print(result["final_response"])
    print()
    
    # 保存结果
    output_file = "agent_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"💾 详细结果已保存到: {output_file}")


if __name__ == "__main__":
    main()

