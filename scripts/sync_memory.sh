#!/bin/bash
# scripts/sync_memory.sh
# 同步 YuanFang 记忆到 OpenClaw
# - 对话摘要 -> ~/.openclaw/workspace/YuanFang_recent_conversations.md
# - 重要信息 -> MEMORY.md

PYTHON="~/.venv-omlx/bin/python"
YF_ROOT="$HOME/YuanFang"
OC_ROOT="$HOME/.openclaw/workspace"

cd "$YF_ROOT"

$PYTHON - << 'SCRIPT' 2>&1
import sys
sys.path.insert(0, '.')
from routes.memory_sync import (
    _read_json, _extract_facts, OPENCLAW_MEMORY, CONVERSATION_LOG, IMPORTANT_NOTES
)
from datetime import datetime, timedelta
import json

logs = _read_json(CONVERSATION_LOG, [])
recent_file = "$OC_ROOT/YuanFang_recent_conversations.md"

# 获取最近7天的对话
cutoff = datetime.now() - timedelta(days=7)
recent_entries = []
for entry in reversed(logs):
    try:
        ts_str = entry.get('timestamp', '')
        ts = datetime.fromisoformat(ts_str)
        if ts >= cutoff:
            recent_entries.append(entry)
    except:
        pass

if not recent_entries:
    print('No conversations to sync')
else:
    # 生成 markdown 摘要
    md_lines = [
        f"# YuanFang 语音对话记录（最近7天）",
        f"自动生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"共 {len(recent_entries)} 条对话",
        "",
    ]
    
    for e in recent_entries[-50:]:  # 最多50条
        ts = e.get('timestamp', '')[:16].replace('T', ' ')
        user = e.get('user_text', '').strip()
        assistant = e.get('assistant_text', '').strip()
        latency = e.get('latency_ms', 0)
        
        if user:
            md_lines.append(f"### {ts}")
            md_lines.append(f"**👤 用户**: {user[:200]}")
        if assistant:
            md_lines.append(f"**🤖 助手**: {assistant[:200]}")
        if latency:
            md_lines.append(f"**⏱ 延迟**: {latency}ms")
        md_lines.append("")
    
    # 提取并同步重要信息到 MEMORY.md
    facts_by_date = {}
    for entry in recent_entries:
        text = entry.get('user_text', '') + ' ' + entry.get('assistant_text', '')
        facts = _extract_facts(text)
        if facts:
            ts = entry.get('timestamp', '')[:10]
            if ts not in facts_by_date:
                facts_by_date[ts] = []
            for f in facts:
                if f not in facts_by_date[ts]:
                    facts_by_date[ts].append(f)
    
    if facts_by_date and OPENCLAW_MEMORY.exists():
        existing = OPENCLAW_MEMORY.read_text('utf-8')
        sync_block = f"\n\n## 🔄 YuanFang 对话同步 ({datetime.now().strftime('%Y-%m-%d %H:00')})\n"
        for date, facts in sorted(facts_by_date.items(), reverse=True):
            sync_block += f"\n### {date}\n"
            for f in facts[:5]:  # 每天最多5条
                sync_block += f"- {f}\n"
        
        if sync_block not in existing:
            OPENCLAW_MEMORY.write_text(existing + sync_block, 'utf-8')
            print(f'Synced facts from {len(facts_by_date)} days to MEMORY.md')
    
    # 写对话摘要
    with open(recent_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    print(f'Updated {recent_file} with {len(recent_entries)} entries')

print('Memory sync complete')
SCRIPT
