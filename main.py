#!/usr/bin/env python3
"""DeepSeek 厨师 Agent - 终端对话入口"""

import sys

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


def main():
    agent = ChefAgent(SYSTEM_PROMPT)
    print("🍳 厨师小D已上线！")
    print("=" * 50)
    print("输入菜名或问题开始聊天。支持的命令：")
    print("  /menu        - 查看全部菜谱")
    print("  /categories  - 查看菜品分类")
    print("  /cook        - 进入做菜模式（分步引导）")
    print("  /reset       - 重置对话")
    print("  exit         - 退出")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 厨师小D：下次想吃什么再找我！")
            break

        if user_input.lower() in ("exit", "quit", "q"):
            print("👋 厨师小D：下次想吃什么再找我！")
            break
        if not user_input:
            continue

        # 处理命令
        if user_input == "/menu":
            print("\n" + list_all_recipes())
            continue
        elif user_input == "/categories":
            print("\n" + list_categories())
            continue
        elif user_input == "/reset":
            agent.reset()
            print("\n🔄 对话已重置，重新开始吧！")
            continue
        elif user_input == "/cook":
            try:
                dish = input("\n🍳 输入菜名开始做菜模式：").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n已取消")
                continue
            result = agent.start_cooking(dish)
            if result:
                print("\n" + result)
                print("\n完成这一步后，输入「下一步」继续。")
            else:
                print(f'\n⚠️ 没找到「{dish}」的菜谱，试试其他菜？')
            continue

        print("\n厨师小D: ", end="", flush=True)
        try:
            response = agent.chat(user_input)
            print(response)
        except Exception as e:
            print(f"⚠️ 出了点小问题: {e}")
            print("请稍后再试。")


if __name__ == "__main__":
    main()
