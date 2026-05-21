"""Agent 核心：DeepSeek API 调用封装 + 菜谱数据库集成"""

import os
from typing import Optional

import httpx

from tools import get_recipe, search_recipes, list_all_recipes

# 优先从环境变量读取，其次从 ~/.hermes/.env 加载（兼容后台 Web 服务器）
_DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not _DEEPSEEK_KEY:
    _env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(_env_path):
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    _DEEPSEEK_KEY = line.split("=", 1)[1].strip("\"'")
                    break
DEEPSEEK_API_KEY = _DEEPSEEK_KEY
BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"
# 本地数据库中已有的菜名列表
KNOWN_DISHES = [
    "鱼香肉丝",
    "西红柿炒鸡蛋",
    "红烧肉",
    "麻婆豆腐",
    "宫保鸡丁",
    "糖醋排骨",
    "青椒炒肉",
    "蒜蓉西兰花",
    "可乐鸡翅",
    "回锅肉",
    "西红柿蛋花汤",
    "紫菜蛋花汤",
    "冬瓜排骨汤",
    "酸辣汤",
    "玉米排骨汤",
]
SEARCH_KEYWORDS = ["怎么做", "做法", "菜谱", "怎么煮", "怎么炒", "怎么烧", "怎样做"]
MENU_KEYWORDS = ["有哪些菜", "全部菜谱", "有什么菜", "菜单"]


class ChefAgent:
    """厨师 Agent，封装 DeepSeek API 调用 + 本地菜谱检索"""

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.messages = [{"role": "system", "content": system_prompt}]
        self.cooking_session = None  # 做菜模式（Task 4 使用）

    def chat(self, user_input: str) -> str:
        """发送用户消息，获取模型回复（自动检索本地菜谱）"""

        # === 做菜模式检测（Task 4 启用）===
        if self._is_cooking_mode():
            return self._handle_cooking_input(user_input)

        # === 检索阶段：如果用户提到已知菜名，先查本地数据库 ===
        recipe_context = ""
        for dish in KNOWN_DISHES:
            if dish in user_input:
                recipe = get_recipe(dish)
                if recipe:
                    recipe_context = (
                        f"\n\n[本地数据库找到菜谱「{dish}」，请以此为准回复]：\n{recipe}"
                    )
                break

        # 没有精确匹配，尝试模糊搜索
        if not recipe_context:
            if any(kw in user_input for kw in SEARCH_KEYWORDS):
                results = search_recipes(user_input)
                if results:
                    recipe_context = f"\n\n[本地数据库相关菜谱]：\n{results}"

        # 用户想浏览菜单
        if not recipe_context:
            if any(kw in user_input for kw in MENU_KEYWORDS):
                recipe_context = f"\n\n[当前菜谱列表]：\n{list_all_recipes()}"

        # === 构建消息 ===
        if recipe_context:
            enhanced_prompt = self.system_prompt + recipe_context
            messages = [
                {"role": "system", "content": enhanced_prompt},
                *self.messages[1:],
                {"role": "user", "content": user_input},
            ]
        else:
            messages = self.messages + [{"role": "user", "content": user_input}]

        # === 调用 API ===
        response = self._call_api(messages)
        assistant_msg = response["choices"][0]["message"]["content"]

        # === 保存到历史 ===
        self.messages.append({"role": "user", "content": user_input})
        self.messages.append({"role": "assistant", "content": assistant_msg})

        return assistant_msg

    def _call_api(self, messages: list) -> dict:
        """调用 DeepSeek Chat API"""
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    def reset(self):
        """重置对话历史（保留 system prompt）"""
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.cooking_session = None

    # === 做菜模式方法（Task 4 实现）===

    def _is_cooking_mode(self) -> bool:
        return self.cooking_session is not None and not self.cooking_session.completed

    def _handle_cooking_input(self, user_input: str) -> str:
        """处理做菜模式下的用户输入"""
        session = self.cooking_session
        if any(kw in user_input for kw in ["下一步", "好了", "继续", "next", "done"]):
            result = session.next_step()
            if session.completed:
                self.cooking_session = None
            return result
        return (
            f"🔔 你正在做 **{session.recipe.name}** 哦！\n\n"
            f"当前进度：{session.progress_text()}\n\n"
            f"准备好了就说「下一步」继续~"
        )

    def start_cooking(self, recipe_name: str) -> Optional[str]:
        """进入做菜模式"""
        from cookmode import CookingSession

        session = CookingSession.start_cooking(recipe_name)
        if not session:
            return None
        self.cooking_session = session
        return session.get_current_step()

    def cooking_next(self) -> Optional[str]:
        """做菜模式下进入下一步"""
        if not self.cooking_session:
            return None
        return self.cooking_session.next_step()
