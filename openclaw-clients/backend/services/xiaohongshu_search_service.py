import logging
logger = logging.getLogger(__name__)
"""
小红书搜索服务
为家庭助手提供小红书内容搜索能力
"""

import subprocess
import json
import re
from typing import List, Dict, Any, Optional


class XiaoHongShuSearchService:
    """小红书搜索服务"""
    
    def __init__(self):
        self.max_results = 10  # 默认返回结果数量
    
    def _parse_mcporter_output(self, output: str) -> List[Dict[str, Any]]:
        """解析 mcporter 输出为结构化数据"""
        results = []
        
        # 提取 JSON 部分（mcporter 输出可能包含日志前缀）
        json_match = re.search(r'\[.*?\]\s*(\{.*\})', output, re.DOTALL)
        if json_match:
            output = json_match.group(1)
        
        try:
            data = json.loads(output)
            feeds = data.get('feeds', [])
            
            for feed in feeds:
                note_card = feed.get('noteCard', {})
                interact_info = note_card.get('interactInfo', {})
                cover = note_card.get('cover', {})
                user = note_card.get('user', {})
                
                results.append({
                    'id': feed.get('id', ''),
                    'title': note_card.get('displayTitle', ''),
                    'type': note_card.get('type', 'normal'),
                    'author': {
                        'user_id': user.get('userId', ''),
                        'nickname': user.get('nickname', '') or user.get('nickName', ''),
                        'avatar': user.get('avatar', '')
                    },
                    'cover_image': cover.get('urlDefault', '') or cover.get('urlPre', ''),
                    'stats': {
                        'likes': interact_info.get('likedCount', '0'),
                        'collects': interact_info.get('collectedCount', '0'),
                        'comments': interact_info.get('commentCount', '0'),
                        'shares': interact_info.get('sharedCount', '0')
                    },
                    'xsec_token': feed.get('xsecToken', ''),
                    'url': f"https://www.xiaohongshu.com/explore/{feed.get('id', '')}"
                })
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误：{e}")
            logger.info(f"原始输出：{output[:500]}")
        
        return results
    
    def search(self, keyword: str, limit: int = 10, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        搜索小红书内容
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量（默认 10）
            filters: 筛选选项（可选）
        
        Returns:
            {
                'success': bool,
                'keyword': str,
                'count': int,
                'results': List[Dict],
                'error': str (if failed)
            }
        """
        try:
            # 构建 mcporter 命令（Python 3.6 兼容语法）
            if filters:
                filters_json = json.dumps(filters)
                command = f'mcporter call xiaohongshu.search_feeds keyword="{keyword}" filters={filters_json}'
            else:
                command = f'mcporter call xiaohongshu.search_feeds keyword="{keyword}"'
            
            # 执行命令（Python 3.6 兼容）
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=30,
                cwd='/home/admin/.openclaw/workspace'
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'keyword': keyword,
                    'count': 0,
                    'results': [],
                    'error': result.stderr.strip() or '搜索失败'
                }
            
            # 解析结果
            feeds = self._parse_mcporter_output(result.stdout)
            
            # 限制返回数量
            if limit and limit > 0:
                feeds = feeds[:limit]
            
            return {
                'success': True,
                'keyword': keyword,
                'count': len(feeds),
                'results': feeds,
                'error': None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'keyword': keyword,
                'count': 0,
                'results': [],
                'error': '搜索超时（>30 秒）'
            }
        except Exception as e:
            return {
                'success': False,
                'keyword': keyword,
                'count': 0,
                'results': [],
                'error': str(e)
            }
    
    def get_feed_detail(self, feed_id: str, xsec_token: str, load_comments: bool = False) -> Dict[str, Any]:
        """
        获取笔记详情
        
        Args:
            feed_id: 笔记 ID
            xsec_token: 访问令牌
            load_comments: 是否加载评论
        
        Returns:
            笔记详情数据
        """
        try:
            if load_comments:
                command = f'mcporter call xiaohongshu.get_feed_detail feed_id="{feed_id}" xsec_token="{xsec_token}" load_all_comments=true'
            else:
                command = f'mcporter call xiaohongshu.get_feed_detail feed_id="{feed_id}" xsec_token="{xsec_token}"'
            
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=30,
                cwd='/home/admin/.openclaw/workspace'
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': result.stderr.strip() or '获取详情失败'
                }
            
            # 解析 JSON
            try:
                json_match = re.search(r'\[.*?\]\s*(\{.*\})', result.stdout, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                else:
                    data = json.loads(result.stdout)
                
                return {
                    'success': True,
                    'data': data
                }
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'JSON 解析失败：{e}'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': '请求超时'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_login_status(self) -> Dict[str, Any]:
        """
        检查小红书登录状态
        
        Returns:
            {
                'logged_in': bool,
                'message': str
            }
        """
        try:
            result = subprocess.run(
                'mcporter call xiaohongshu.check_login_status',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=10,
                cwd='/home/admin/.openclaw/workspace'
            )
            
            output = result.stdout.strip()
            logged_in = '已登录' in output or 'logged' in output.lower()
            
            return {
                'logged_in': logged_in,
                'message': output
            }
            
        except Exception as e:
            return {
                'logged_in': False,
                'message': f'检查失败：{str(e)}'
            }


# 快速测试
if __name__ == '__main__':
    service = XiaoHongShuSearchService()
    
    logger.info("=== 小红书搜索服务测试 ===\n")
    
    # 检查登录状态
    logger.info("1. 检查登录状态...")
    status = service.check_login_status()
    logger.info(f"   状态：{status['message']}\n")
    
    # 搜索测试
    logger.info("2. 搜索测试（美食推荐）...")
    result = service.search("美食推荐", limit=3)
    
    if result['success']:
        logger.info(f"   找到 {result['count']} 条结果\n")
        for i, item in enumerate(result['results'], 1):
            logger.info(f"   [{i}] {item['title']}")
            logger.info(f"       作者：{item['author']['nickname']}")
            logger.info(f"       点赞：{item['stats']['likes']} | 收藏：{item['stats']['collects']}")
            logger.info(f"       链接：{item['url']}\n")
    else:
        logger.error(f"   搜索失败：{result['error']}\n")
