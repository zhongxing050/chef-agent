"""做菜模式 - 分步骤引导用户完成烹饪"""

import time
from typing import Optional

from recipes import Recipe, RecipeDB
from tools import get_recipe


class CookingSession:
    """一次做菜引导会话"""

    def __init__(self, recipe: Recipe):
        self.recipe = recipe
        self.current_step = 0
        self.total_steps = len(recipe.steps)
        self.started_at = time.time()
        self.completed = False

    def get_current_step(self) -> Optional[str]:
        """获取当前步骤的描述"""
        if self.current_step >= self.total_steps:
            return None
        step = self.recipe.steps[self.current_step]
        text = f"## 步骤 {step.order}/{self.total_steps}"
        text += f"\n\n**{step.description}**"
        if step.duration:
            text += f"\n⏱ 预计 {step.duration}"
        if step.tip:
            text += f"\n💡 *{step.tip}*"
        return text

    def next_step(self) -> Optional[str]:
        """进入下一步，返回下一步描述或完成消息"""
        self.current_step += 1
        if self.current_step >= self.total_steps:
            self.completed = True
            elapsed = int(time.time() - self.started_at)
            minutes = elapsed // 60
            tip_msg = (
                self.recipe.tips[0]
                if self.recipe.tips
                else "享受你的美食吧！"
            )
            return (
                f"## 🎉 完成！\n\n"
                f"恭喜你完成了 **{self.recipe.name}**！"
                f"（用时约 {minutes} 分钟）\n\n"
                f"💡 {tip_msg}"
            )
        return self.get_current_step()

    def progress_text(self) -> str:
        """进度条文本"""
        done = self.current_step
        total = self.total_steps
        bar = "█" * done + "░" * (total - done)
        return f"{bar} {done}/{total}"

    @staticmethod
    def start_cooking(recipe_name: str) -> Optional["CookingSession"]:
        """通过菜名开始做菜模式"""
        db = RecipeDB()
        results = db.search_by_name(recipe_name)
        if not results:
            return None
        return CookingSession(results[0])
