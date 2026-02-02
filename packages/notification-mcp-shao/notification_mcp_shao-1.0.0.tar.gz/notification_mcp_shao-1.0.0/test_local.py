#!/usr/bin/env python3
"""
本地测试脚本 - 在发布前测试功能

@author shao
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入服务器模块
import sys
sys.path.insert(0, 'src')

from notification_mcp.server import EmailSender, DingTalkSender

async def test_email():
    """测试邮件发送"""
    print("=" * 60)
    print("📧 测试邮件发送")
    print("=" * 60)
    
    sender = EmailSender()
    result = sender.send_email(
        to=os.getenv("EMAIL_ACCOUNT"),
        subject="本地测试邮件",
        content="这是一封本地测试邮件，用于验证 UVX 包功能"
    )
    
    print(f"结果: {result}")
    print()

async def test_dingtalk():
    """测试钉钉消息"""
    print("=" * 60)
    print("🤖 测试钉钉消息")
    print("=" * 60)
    
    sender = DingTalkSender()
    result = sender.send_dingtalk_message(
        title="本地测试",
        text="这是一条本地测试消息，用于验证 UVX 包功能"
    )
    
    print(f"结果: {result}")
    print()

async def main():
    print("\n🚀 开始本地测试...\n")
    
    await test_email()
    await test_dingtalk()
    
    print("✅ 本地测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
