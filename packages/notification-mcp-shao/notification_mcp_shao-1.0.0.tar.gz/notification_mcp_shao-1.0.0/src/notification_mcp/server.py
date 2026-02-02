#!/usr/bin/env python3
"""
MCP通知服务器 - UVX 版本

@author shao
"""

import os
import sys
import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import requests
from typing import Optional, List, Dict, Any
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# 设置详细的日志记录
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/mcp_notification_server.log"),
    ],
)
logger = logging.getLogger(__name__)


class Config:
    """配置类，从环境变量读取配置"""
    
    SMTP_CONFIG = {
        "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "account": os.getenv("EMAIL_ACCOUNT", ""),
        "password": os.getenv("EMAIL_PASSWORD", ""),
        "use_ssl": os.getenv("SMTP_SSL", "false").lower() == "true",
    }
    
    DINGTALK_CONFIG = {
        "webhook": os.getenv("DINGTALK_WEBHOOK", ""),
        "secret": os.getenv("DINGTALK_SECRET", ""),
    }


class EmailSender:
    """邮件发送类"""
    
    def __init__(self):
        self.smtp_config = Config.SMTP_CONFIG
        self.validate_config()

    def validate_config(self):
        required = ["server", "port", "account", "password"]
        missing = []
        for key in required:
            if not self.smtp_config.get(key):
                missing.append(key)

        if missing:
            logger.error(f"❌ SMTP配置缺少必要参数: {missing}")
        else:
            logger.info("✅ SMTP配置验证通过")

    def send_email(
        self,
        to: str,
        subject: str,
        content: str,
        content_type: str = "plain",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        try:
            logger.info(f"📧 尝试发送邮件到: {to}, 主题: {subject}")

            if not all(
                [self.smtp_config.get("account"), self.smtp_config.get("password")]
            ):
                error_msg = "SMTP账号或密码未配置"
                logger.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg, "message": error_msg}

            if content_type == "html":
                msg = MIMEMultipart()
                msg.attach(MIMEText(content, "html", "utf-8"))
            else:
                msg = MIMEText(content, content_type, "utf-8")

            msg["From"] = Header(
                f"Notification System <{self.smtp_config['account']}>", "utf-8"
            )
            msg["To"] = Header(to, "utf-8")
            msg["Subject"] = Header(subject, "utf-8")

            if cc:
                msg["Cc"] = Header(", ".join(cc), "utf-8")

            logger.info(
                f"🔗 连接到SMTP服务器: {self.smtp_config['server']}:{self.smtp_config['port']}, SSL: {self.smtp_config.get('use_ssl', False)}"
            )

            if self.smtp_config.get("use_ssl", False):
                server = smtplib.SMTP_SSL(
                    self.smtp_config["server"], self.smtp_config["port"], timeout=30
                )
                logger.info("✅ 使用 SMTP_SSL 连接")
            else:
                server = smtplib.SMTP(
                    self.smtp_config["server"], self.smtp_config["port"], timeout=30
                )
                logger.info("✅ 使用 SMTP 连接，准备 STARTTLS")
                server.starttls()

            server.ehlo()
            logger.info(f"🔐 登录SMTP账号: {self.smtp_config['account'][:3]}***")
            server.login(self.smtp_config["account"], self.smtp_config["password"])
            logger.info("✅ SMTP 登录成功")

            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            logger.info(f"📤 发送邮件给 {len(recipients)} 个收件人")
            server.sendmail(self.smtp_config["account"], recipients, msg.as_string())
            server.quit()

            logger.info(f"✅ 邮件发送成功到: {to}")
            return {
                "success": True,
                "message": f"邮件发送成功到 {to}",
                "recipients": recipients,
            }

        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"邮件发送失败: {str(e)}",
            }


class DingTalkSender:
    """钉钉消息发送类"""
    
    def __init__(self):
        self.dingtalk_config = Config.DINGTALK_CONFIG
        self.validate_config()

    def validate_config(self):
        if not self.dingtalk_config.get("webhook"):
            logger.warning("⚠️ 钉钉配置缺少webhook URL")
        else:
            logger.info("✅ 钉钉配置验证通过")

    def send_dingtalk_message(
        self,
        title: str,
        text: str,
        msg_type: str = "markdown",
        at_mobiles: Optional[List[str]] = None,
        at_all: bool = False,
    ) -> Dict[str, Any]:
        try:
            logger.info(f"🤖 尝试发送钉钉消息: {title}")

            if not self.dingtalk_config.get("webhook"):
                error_msg = "钉钉webhook未配置"
                logger.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg, "message": error_msg}

            headers = {"Content-Type": "application/json"}

            if msg_type == "text":
                data = {
                    "msgtype": "text",
                    "text": {"content": text},
                    "at": {"atMobiles": at_mobiles or [], "isAtAll": at_all},
                }
            else:
                data = {
                    "msgtype": "markdown",
                    "markdown": {"title": title, "text": f"### {title}\n\n{text}"},
                    "at": {"atMobiles": at_mobiles or [], "isAtAll": at_all},
                }

            webhook_url = self.dingtalk_config["webhook"]
            secret = self.dingtalk_config.get("secret")

            if secret:
                import time
                import hmac
                import hashlib
                import base64
                import urllib.parse

                timestamp = str(round(time.time() * 1000))
                secret_enc = secret.encode("utf-8")
                string_to_sign = f"{timestamp}\n{secret}"
                string_to_sign_enc = string_to_sign.encode("utf-8")
                hmac_code = hmac.new(
                    secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
                ).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
                logger.info(f"🔐 使用加签的钉钉webhook")

            logger.info(f"🔗 发送钉钉消息到: {webhook_url[:50]}...")
            response = requests.post(
                webhook_url, headers=headers, data=json.dumps(data), timeout=10
            )
            result = response.json()

            if result.get("errcode") == 0:
                logger.info(f"✅ 钉钉消息发送成功: {title}")
                return {
                    "success": True,
                    "message": f"钉钉消息发送成功: {title}",
                    "result": result,
                }
            else:
                logger.error(f"❌ 钉钉消息发送失败: {result}")
                return {
                    "success": False,
                    "error": result.get("errmsg", "未知错误"),
                    "result": result,
                }

        except Exception as e:
            logger.error(f"❌ 钉钉消息发送异常: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"钉钉消息发送异常: {str(e)}",
            }


async def run_server():
    """运行 MCP 服务器"""
    logger.info("🚀 启动MCP通知服务器...")

    try:
        email_sender = EmailSender()
        dingtalk_sender = DingTalkSender()

        server = Server("notification-server")
        logger.info("✅ MCP服务器实例创建成功")

        @server.list_tools()
        async def handle_list_tools():
            logger.info("📋 处理工具列表请求")
            from mcp.types import Tool
            
            return [
                Tool(
                    name="send_email",
                    description="发送电子邮件到指定邮箱",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "to": {"type": "string", "description": "收件人邮箱地址"},
                            "subject": {"type": "string", "description": "邮件主题"},
                            "content": {
                                "type": "string",
                                "description": "邮件正文内容",
                            },
                            "content_type": {
                                "type": "string",
                                "enum": ["plain", "html"],
                                "description": "内容类型：plain(纯文本)或html(HTML格式)",
                                "default": "plain",
                            },
                            "cc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "抄送邮箱地址列表",
                                "default": [],
                            },
                            "bcc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "密送邮箱地址列表",
                                "default": [],
                            },
                        },
                        "required": ["to", "subject", "content"],
                    },
                ),
                Tool(
                    name="send_dingtalk_message",
                    description="发送消息到钉钉群",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "消息标题"},
                            "text": {"type": "string", "description": "消息正文内容"},
                            "msg_type": {
                                "type": "string",
                                "enum": ["text", "markdown"],
                                "description": "消息类型：text(文本)或markdown(Markdown格式)",
                                "default": "markdown",
                            },
                            "at_mobiles": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "要@的手机号列表",
                                "default": [],
                            },
                            "at_all": {
                                "type": "boolean",
                                "description": "是否@所有人",
                                "default": False,
                            },
                        },
                        "required": ["title", "text"],
                    },
                ),
            ]

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]):
            logger.info(f"🔨 调用工具: {name}, 参数: {json.dumps(arguments)[:100]}...")
            from mcp.types import TextContent

            if name == "send_email":
                result = email_sender.send_email(
                    to=arguments["to"],
                    subject=arguments["subject"],
                    content=arguments["content"],
                    content_type=arguments.get("content_type", "plain"),
                    cc=arguments.get("cc", []),
                    bcc=arguments.get("bcc", []),
                )
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            elif name == "send_dingtalk_message":
                result = dingtalk_sender.send_dingtalk_message(
                    title=arguments["title"],
                    text=arguments["text"],
                    msg_type=arguments.get("msg_type", "markdown"),
                    at_mobiles=arguments.get("at_mobiles", []),
                    at_all=arguments.get("at_all", False),
                )
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            else:
                error_msg = f"未知工具: {name}"
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)

        logger.info("🌐 启动MCP服务器，等待连接...")

        # 正确创建notification_options和experimental_capabilities
        try:
            from mcp.types import NotificationOptions

            notification_options = NotificationOptions(tools_changed=True)
            experimental_capabilities = {}

            logger.info("✅ 使用正确的NotificationOptions类型")
            capabilities = server.get_capabilities(
                notification_options, experimental_capabilities
            )

        except ImportError:
            logger.warning("⚠️ 无法导入NotificationOptions，尝试替代方案")

            class SimpleNotificationOptions:
                tools_changed = True

            notification_options = SimpleNotificationOptions()
            experimental_capabilities = {}
            capabilities = server.get_capabilities(
                notification_options, experimental_capabilities
            )

        logger.info(f"📊 获取到的capabilities: {type(capabilities)}")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="notification-mcp-server",
                    server_version="1.0.0",
                    capabilities=capabilities,
                ),
            )

    except Exception as e:
        logger.error(f"💥 MCP服务器启动失败: {str(e)}", exc_info=True)
        raise


def main():
    """主入口函数"""
    import asyncio

    logger.info("=" * 50)
    logger.info("🎯 MCP通知服务器启动 (UVX版本)")
    logger.info("=" * 50)

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("\n🛑 MCP服务器已停止")
    except Exception as e:
        logger.error(f"💥 MCP服务器启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
