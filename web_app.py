#!/usr/bin/env python3
"""厨师小D - Web 服务器"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

# 确保项目目录在路径中
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(title="厨师小D")

# 只在有 API Key 时加载 Agent
agent = None
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if DEEPSEEK_API_KEY:
    from agent import ChefAgent
    from tools import list_all_recipes, list_categories

    SYSTEM_PROMPT = """你是「厨师小D」，一个热情专业的AI厨师助手。

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

    agent = ChefAgent(SYSTEM_PROMPT)
else:
    from tools import list_all_recipes, list_categories
    print("⚠️ 未设置 DEEPSEEK_API_KEY，Agent 将使用本地菜谱数据模式")


BASE_DIR = Path(__file__).parent


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    cooking: bool = False
    cooking_completed: bool = False


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = BASE_DIR / "static" / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>厨师小D</h1><p>页面加载失败</p>")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 处理菜单命令
    if msg == "/menu":
        return ChatResponse(reply=list_all_recipes())
    if msg == "/categories":
        return ChatResponse(reply=list_categories())

    # 处理 /cook 命令
    if msg.startswith("/cook "):
        dish = msg[6:].strip()
        if not agent:
            return ChatResponse(reply="⚠️ 未设置 DEEPSEEK_API_KEY，无法使用做菜模式")
        from cookmode import CookingSession
        session = CookingSession.start_cooking(dish)
        if not session:
            return ChatResponse(reply=f"⚠️ 没找到「{dish}」的菜谱，试试其他菜？")
        agent.cooking_session = session
        step = session.get_current_step()
        return ChatResponse(reply=step if step else "开始吧！", cooking=True)

    # 处理 /reset
    if msg == "/reset":
        if agent:
            agent.reset()
        return ChatResponse(reply="🔄 对话已重置，重新开始吧！")

    # 调用 Agent
    if agent:
        if agent._is_cooking_mode():
            if any(kw in msg for kw in ["下一步", "好了", "继续", "next", "done"]):
                result = agent._handle_cooking_input(msg)
                completed = agent.cooking_session is None or (
                    agent.cooking_session and agent.cooking_session.completed
                )
                return ChatResponse(reply=result, cooking=not completed,
                                    cooking_completed=completed)
            else:
                cs = agent.cooking_session
                if cs is None:
                    return ChatResponse(reply="做菜会话已结束")
                return ChatResponse(reply=(
                    f"🔔 你正在做 **{cs.recipe.name}** 哦！\n\n"
                    f"当前进度：{cs.progress_text()}\n\n"
                    f"准备好了就说「下一步」继续~"
                ), cooking=True)
        reply = agent.chat(msg)
    else:
        reply = "⚠️ 未设置 DEEPSEEK_API_KEY，请先设置环境变量后才能使用 AI 对话功能。\n\n本地菜谱数据已加载，可以使用 `/menu` 查看。"
    return ChatResponse(reply=reply)


if __name__ == "__main__":
    import uvicorn
    port = 8899
    print(f"🍳 厨师小D服务启动: http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
