# Notification MCP Server

MCP 服务器，用于发送邮件和钉钉消息通知。

## 功能

- 📧 发送邮件（支持 SMTP）
- 🤖 发送钉钉消息（支持 Markdown 格式）

## 安装

使用 uvx 运行（推荐）：
```bash
uvx notification-mcp-server@latest
```

或使用 pip 安装：
```bash
pip install notification-mcp-server
```

## 配置

需要设置以下环境变量：

### 邮件配置
- `SMTP_SERVER`: SMTP 服务器地址（如 smtp.163.com）
- `SMTP_PORT`: SMTP 端口（如 465）
- `EMAIL_ACCOUNT`: 邮箱账号
- `EMAIL_PASSWORD`: 邮箱授权码
- `SMTP_SSL`: 是否使用 SSL（true/false）

### 钉钉配置
- `DINGTALK_WEBHOOK`: 钉钉机器人 Webhook URL
- `DINGTALK_SECRET`: 钉钉机器人加签密钥（可选）

## 在 Kiro IDE 中使用

在 `.kiro/settings/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "notification": {
      "command": "uvx",
      "args": ["notification-mcp-server@latest"],
      "env": {
        "SMTP_SERVER": "smtp.163.com",
        "SMTP_PORT": "465",
        "EMAIL_ACCOUNT": "your@email.com",
        "EMAIL_PASSWORD": "your-auth-code",
        "SMTP_SSL": "true",
        "DINGTALK_WEBHOOK": "your-webhook-url"
      }
    }
  }
}
```

## 可用工具

### send_email
发送邮件到指定邮箱。

参数：
- `to`: 收件人邮箱地址
- `subject`: 邮件主题
- `content`: 邮件内容
- `content_type`: 内容类型（plain/html，默认 plain）
- `cc`: 抄送列表（可选）
- `bcc`: 密送列表（可选）

### send_dingtalk_message
发送消息到钉钉群。

参数：
- `title`: 消息标题
- `text`: 消息内容
- `msg_type`: 消息类型（text/markdown，默认 markdown）
- `at_mobiles`: @的手机号列表（可选）
- `at_all`: 是否@所有人（可选）

## 作者

@author shao

## 许可证

MIT
