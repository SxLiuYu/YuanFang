"""配置命令模块"""

from typing import Dict, Any
import os
import json


DEFAULT_CONFIG = {
    'server': 'http://localhost:8082',
    'sync_interval': 300,  # 5分钟
    'data_types': {
        'location': True,
        'health': True,
        'calendar': True,
        'notification': False,
        'app_usage': False
    },
    'privacy': {
        'local_only': True,
        'encrypt': True,
        'auto_clean_days': 30
    }
}


def get_config_path() -> str:
    """获取配置文件路径"""
    config_dir = os.path.expanduser('~/.openclaw')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.json')


def load_config() -> Dict[str, Any]:
    """加载配置"""
    config_path = get_config_path()
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """保存配置"""
    config_path = get_config_path()
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def show_config() -> None:
    """显示当前配置"""
    config = load_config()
    
    print("当前配置:")
    print(f"  服务器: {config.get('server')}")
    print(f"  同步间隔: {config.get('sync_interval')}秒")
    print(f"\n数据类型:")
    for dtype, enabled in config.get('data_types', {}).items():
        status = "✓" if enabled else "✗"
        print(f"  {status} {dtype}")
    print(f"\n隐私设置:")
    privacy = config.get('privacy', {})
    print(f"  仅本地: {'是' if privacy.get('local_only') else '否'}")
    print(f"  加密: {'是' if privacy.get('encrypt') else '否'}")
    print(f"  自动清理: {privacy.get('auto_clean_days')}天")


def set_config(key: str, value: str) -> None:
    """设置配置项"""
    config = load_config()
    
    # 解析key路径
    keys = key.split('.')
    
    # 设置值
    current = config
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    # 转换值类型
    if value.lower() == 'true':
        value = True
    elif value.lower() == 'false':
        value = False
    elif value.isdigit():
        value = int(value)
    
    current[keys[-1]] = value
    
    save_config(config)
    print(f"已设置 {key} = {value}")