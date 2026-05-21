"""菜谱数据库 - 检索和加载"""

import json
import os
from typing import List, Optional

from recipes.schema import Recipe


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class RecipeDB:
    """菜谱数据库类，自动加载 data/ 目录下所有 JSON 菜谱文件"""

    def __init__(self):
        self.recipes: List[Recipe] = []
        self._load_all()

    def _load_all(self):
        """加载 data/ 目录下所有 JSON 菜谱文件"""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
            return

        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(DATA_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("recipes", []):
                    self.recipes.append(Recipe.from_dict(item))

    def search_by_name(self, keyword: str) -> List[Recipe]:
        """按菜名搜索（模糊匹配）"""
        keyword = keyword.lower()
        return [r for r in self.recipes if keyword in r.name.lower()]

    def search_by_tag(self, tag: str) -> List[Recipe]:
        """按标签搜索"""
        tag = tag.lower()
        return [r for r in self.recipes if any(tag in t.lower() for t in r.tags)]

    def search_by_ingredient(self, ingredient: str) -> List[Recipe]:
        """按食材搜索"""
        ingredient = ingredient.lower()
        return [
            r for r in self.recipes
            if any(ingredient in i.name.lower() for i in r.ingredients)
        ]

    def get_by_id(self, recipe_id: str) -> Optional[Recipe]:
        """按 ID 精确查找"""
        for r in self.recipes:
            if r.id == recipe_id:
                return r
        return None

    def get_all(self) -> List[Recipe]:
        """获取所有菜谱"""
        return self.recipes

    def format_recipe(self, recipe: Recipe) -> str:
        """将菜谱格式化为可读文本"""
        lines = [
            f"## {recipe.name}",
            f"**{recipe.description}**",
            "",
            f"- ⏱ 准备: {recipe.prep_time} | 烹饪: {recipe.cook_time} | 难度: {recipe.difficulty}",
            f"- 🍽️ 份量: {recipe.servings} 人份",
            "",
            "### 📋 食材",
        ]
        for ing in recipe.ingredients:
            note = f"（{ing.note}）" if ing.note else ""
            lines.append(f"- {ing.name} **{ing.amount}** {note}")

        lines.append("")
        lines.append("### 👨‍🍳 步骤")
        for step in recipe.steps:
            tip = f"\n  💡 *{step.tip}*" if step.tip else ""
            dur = f" ⏱ {step.duration}" if step.duration else ""
            lines.append(f"**{step.order}.** {step.description}{dur}{tip}")

        if recipe.tips:
            lines.append("")
            lines.append("### 💡 小贴士")
            for tip in recipe.tips:
                lines.append(f"- {tip}")

        return "\n".join(lines)
