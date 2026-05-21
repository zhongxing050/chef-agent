#!/usr/bin/env python3
"""厨师小D - Web API 服务器"""

import os
import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from agent import ChefAgent
from tools import list_all_recipes, list_categories, search_recipes, get_recipe
from recipes import RecipeDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chef-agent")

app = FastAPI(title="厨师小D")

# CORS 允许本地访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 Agent 实例
system_prompt = """你是「厨师小D」，一个热情专业的AI厨师助手。

你的特点：
1. 精通中餐、西餐、烘焙等多种菜系
2. 讲解做菜步骤清晰明了，分步骤引导用户
3. 会给出实用的烹饪技巧和食材替换建议
4. 语气亲切友好，像一位真实的大厨在厨房里带着用户做菜
5. 回答简洁实用，避免过于抽象的理论

当用户问菜谱时，你会：
- 先确认用户想做什么菜
- 列出所需食材和用量
- 分步骤讲解烹饪过程
- 提醒关键注意事项

你的菜谱数据库中有以下菜谱（优先用数据库中的结构化数据回答）：
- 家常菜：鱼香肉丝、西红柿炒鸡蛋、红烧肉、麻婆豆腐、宫保鸡丁、糖醋排骨、青椒炒肉、蒜蓉西兰花、可乐鸡翅、回锅肉
- 汤/炖菜：西红柿蛋花汤、紫菜蛋花汤、冬瓜排骨汤、酸辣汤、玉米排骨汤

如果用户问的菜不在数据库中，你同样可以根据你的知识回答。"""

agent = ChefAgent(system_prompt)
db = RecipeDB()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    mode: str = "chat"


# ── API ──────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    """普通对话"""
    msg = req.message.strip()
    if not msg:
        raise HTTPException(400, "消息不能为空")

    logger.info(f"用户: {msg}")

    # 特殊命令处理
    if msg == "/menu":
        return ChatResponse(reply=list_all_recipes(), mode="menu")
    if msg == "/categories":
        return ChatResponse(reply=list_categories(), mode="categories")
    if msg == "/reset":
        agent.reset()
        return ChatResponse(reply="🔄 对话已重置，重新开始吧！", mode="reset")

    # 做菜模式启动
    if msg.startswith("/cook "):
        dish = msg[6:].strip()
        result = agent.start_cooking(dish)
        if result:
            return ChatResponse(reply=result, mode="cooking")
        return ChatResponse(reply=f'⚠️ 没找到「{dish}」的菜谱，试试其他菜？', mode="error")

    # 如果是做菜模式中
    if agent._is_cooking_mode():
        if msg in ["下一步", "好了", "继续", "next", "done"]:
            result = agent.cooking_next()
            if result:
                return ChatResponse(reply=result, mode="cooking")
        return ChatResponse(
            reply=f"🔔 你正在做菜呢！说「下一步」继续~",
            mode="cooking",
        )

    # 普通聊天
    try:
        reply = agent.chat(msg)
        return ChatResponse(reply=reply, mode="chat")
    except Exception as e:
        logger.error(f"API 错误: {e}")
        return ChatResponse(
            reply=f"⚠️ 出错了：{str(e)}\n\n请检查 DEEPSEEK_API_KEY 是否正确配置。",
            mode="error",
        )


@app.get("/api/recipes")
async def list_recipes():
    """获取所有菜谱列表"""
    recipes = []
    for r in db.get_all():
        recipes.append({
            "id": r.id,
            "name": r.name,
            "category": r.category,
            "difficulty": r.difficulty,
            "prep_time": r.prep_time,
            "cook_time": r.cook_time,
            "description": r.description,
            "tags": r.tags,
        })
    return {"recipes": recipes, "total": len(recipes)}


@app.get("/api/recipe/{name}")
async def recipe_detail(name: str):
    """获取菜谱详情"""
    r = get_recipe(name)
    if r:
        return {"recipe": r}
    raise HTTPException(404, f"未找到「{name}」")


@app.get("/")
async def index():
    """返回聊天界面"""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return HTMLResponse(open(index_path, encoding="utf-8").read())
    return {"error": "前端文件未找到"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("CHEF_PORT", 8899))
    print(f"🍳 厨师小D服务启动: http://127.0.0.1:{port}")
    print(f"   打开浏览器访问即可聊天")
    print(f"   支持命令: /menu, /categories, /cook 菜名, /reset")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
