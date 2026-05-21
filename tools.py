"""Agent 工具函数 - 菜谱检索"""

from typing import List, Optional
from recipes import RecipeDB

db = RecipeDB()


def search_recipes(query: str) -> str:
    """搜索菜谱，按菜名/食材/标签多维度匹配，返回格式化结果"""
    by_name = db.search_by_name(query)
    by_ingredient = db.search_by_ingredient(query)
    by_tag = db.search_by_tag(query)

    # 合并去重
    seen = set()
    results = []
    for r in by_name + by_ingredient + by_tag:
        if r.id not in seen:
            seen.add(r.id)
            results.append(r)

    if not results:
        return ""

    lines = [f"找到 {len(results)} 道相关菜谱：\n"]
    for r in results:
        lines.append(
            f"- **{r.name}**（{r.difficulty}，{r.prep_time}+{r.cook_time}）"
        )
    return "\n".join(lines)


def get_recipe(name: str) -> Optional[str]:
    """精确查找一道菜谱（先按 ID，再按菜名模糊匹配），返回完整格式化内容"""
    r = db.get_by_id(name)
    if r:
        return db.format_recipe(r)
    results = db.search_by_name(name)
    if results:
        return db.format_recipe(results[0])
    return None


def list_categories() -> str:
    """列出所有菜谱分类"""
    categories = set(r.category for r in db.get_all())
    return "📂 当前菜谱分类：\n" + "\n".join(f"- {c}" for c in sorted(categories))


def list_all_recipes() -> str:
    """列出所有菜谱及简介"""
    lines = ["🍳 全部菜谱：\n"]
    for r in db.get_all():
        lines.append(f"- **{r.name}** — {r.description}")
    return "\n".join(lines)
