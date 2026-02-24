"""
抖音热搜插件
获取抖音实时热搜榜
"""

import re
from datetime import datetime

from astrbot.api import logger
from astrbot.api.event.filter import command, regex
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context, Star


class DouyinHotPlugin(Star):
    """抖音热搜插件"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "https://v2.xxapi.cn/api/douyinhot"
        self.default_count = 10
        self.max_count = 50
    
    async def initialize(self):
        logger.info("抖音热搜插件已加载")
    
    async def fetch_douyin_hot(self):
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.api_url)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict):
                        return data.get('data', []) or data.get('list', []) or []
                    elif isinstance(data, list):
                        return data
                return []
        except Exception as e:
            logger.error(f"获取抖音热搜失败: {e}")
            return []
    
    def generate_text_report(self, hot_list, count):
        text_lines = ["抖音热搜榜"]
        actual_count = min(count, len(hot_list))
        
        for idx, item in enumerate(hot_list[:actual_count]):
            rank = idx + 1
            title = item.get('word', item.get('title', item.get('name', '未知')))
            hot_value = item.get('hot_value', item.get('hot', item.get('value', '')))
            
            text_lines.append(f"{rank}. {title}")
            if hot_value:
                text_lines.append(f"   热度：{hot_value}")
        
        text_lines.append(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(text_lines)
    
    @command("douyinhot")
    async def handle_douyin_hot_command(self, event):
        try:
            count = self.default_count
            
            if hasattr(event, 'message_str'):
                msg_text = event.message_str
                match = re.search(r'(?:douyinhot|抖音热搜)\s+(\d+)', msg_text, re.IGNORECASE)
                if match:
                    count = int(match.group(1))
                    if count < 1:
                        count = 1
                    if count > 50:
                        count = 50
            
            hot_list = await self.fetch_douyin_hot()
            
            if not hot_list:
                await event.send(event.plain_result("获取热搜数据失败"))
                return
            
            text_result = self.generate_text_report(hot_list, count)
            await event.send(event.plain_result(text_result))
            
        except Exception as e:
            logger.error(f"处理失败: {e}")
            await event.send(event.plain_result(f"处理失败: {str(e)}"))
    
    @regex(r"(抖音热搜)")
    async def handle_douyin_hot_regex(self, event):
        try:
            await self.handle_douyin_hot_command(event)
        except Exception as e:
            logger.error(f"正则匹配处理失败: {e}")