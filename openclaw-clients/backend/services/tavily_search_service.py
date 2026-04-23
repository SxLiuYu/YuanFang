"""
Tavily Search Service
使用 Tavily API 进行网络搜索，专为 AI 应用优化的搜索服务
"""

import os
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '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')
TAVILY_BASE_URL = 'https://api.tavily.com'


class TavilySearchService:
    """
    Tavily 搜索服务
    文档: https://docs.tavily.com/
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or TAVILY_API_KEY
        if not self.api_key:
            logger.warning("TAVILY_API_KEY 未配置")
    
    def search(
        self,
        query: str,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = True,
        include_raw_content: bool = False,
        max_results: int = 5
    ) -> Dict:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            search_depth: "basic" 或 "advanced" (advanced 更深入但更慢)
            include_domains: 仅搜索指定域名
            exclude_domains: 排除指定域名
            include_answer: 是否包含 AI 生成的答案
            include_raw_content: 是否包含原始 HTML
            max_results: 最大结果数 (1-10)
        
        Returns:
            {
                "answer": "AI 生成的答案",
                "results": [
                    {
                        "title": "标题",
                        "url": "链接",
                        "content": "内容摘要",
                        "score": "相关性分数"
                    }
                ]
            }
        """
        if not self.api_key:
            return {"error": "TAVILY_API_KEY 未配置", "results": []}
        
        url = f"{TAVILY_BASE_URL}/search"
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "max_results": max_results
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Tavily 搜索成功: {query}, 结果数: {len(data.get('results', []))}")
            
            return {
                "success": True,
                "answer": data.get("answer", ""),
                "results": data.get("results", []),
                "query": query
            }
            
        except requests.exceptions.Timeout:
            logger.error("Tavily 搜索超时")
            return {"error": "搜索超时", "results": []}
        except requests.exceptions.RequestException as e:
            logger.error(f"Tavily 搜索失败: {e}")
            return {"error": str(e), "results": []}
    
    def search_news(self, query: str, max_results: int = 5) -> Dict:
        """搜索新闻 (使用 advanced 深度)"""
        return self.search(
            query=query,
            search_depth="advanced",
            include_answer=True,
            max_results=max_results
        )
    
    def search_quick(self, query: str) -> str:
        """快速搜索，仅返回答案"""
        result = self.search(query, include_answer=True, max_results=3)
        if result.get("answer"):
            return result["answer"]
        elif result.get("results"):
            return result["results"][0].get("content", "")
        return "未找到相关信息"
    
    def search_with_context(self, query: str, max_results: int = 5) -> str:
        """
        搜索并返回格式化的上下文
        用于 AI 对话上下文
        """
        result = self.search(query, include_answer=True, max_results=max_results)
        
        if not result.get("results"):
            return ""
        
        context_parts = []
        
        if result.get("answer"):
            context_parts.append(f"【摘要】{result['answer']}")
        
        context_parts.append("\n【详细来源】")
        for i, item in enumerate(result["results"][:3], 1):
            context_parts.append(f"{i}. {item.get('title', '未知标题')}")
            context_parts.append(f"   {item.get('content', '')[:200]}...")
            context_parts.append(f"   来源: {item.get('url', '')}")
        
        return "\n".join(context_parts)


tavily_service = TavilySearchService()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Tavily Search 测试 ===\n")
    
    result = tavily_service.search("Python 异步编程最佳实践")
    
    if result.get("answer"):
        print(f"答案: {result['answer']}\n")
    
    print("搜索结果:")
    for item in result.get("results", []):
        print(f"- {item['title']}")
        print(f"  {item['url']}")
        print(f"  {item['content'][:100]}...\n")