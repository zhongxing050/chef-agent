"""菜谱数据结构定义"""

from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class Ingredient:
    """食材类"""
    name: str          # 食材名称
    amount: str        # 用量（如 "300克", "2勺"）
    note: str = ""     # 备注（如 "可选", "可用猪肉代替"）


@dataclass
class Step:
    """步骤类"""
    order: int         # 步骤序号
    description: str   # 步骤描述
    tip: str = ""      # 小贴士（可选）
    duration: str = "" # 预计时间（如 "5分钟"）


@dataclass
class Recipe:
    """菜品类"""
    id: str                     # 唯一标识
    name: str                   # 菜名
    category: str               # 分类（家常菜/汤/烘焙等）
    difficulty: str             # 难度（简单/中等/困难）
    prep_time: str              # 准备时间
    cook_time: str              # 烹饪时间
    servings: int               # 份量（几人份）
    ingredients: List[Ingredient]  # 食材列表
    steps: List[Step]           # 步骤列表
    tags: List[str] = field(default_factory=list)      # 标签（辣/酸甜/快手等）
    tips: List[str] = field(default_factory=list)      # 整体提示
    description: str = ""       # 菜品简介

    def to_dict(self):
        """将 Recipe 对象转为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        """从字典构建 Recipe 对象"""
        data["ingredients"] = [Ingredient(**i) for i in data["ingredients"]]
        data["steps"] = [Step(**s) for s in data["steps"]]
        return cls(**data)
