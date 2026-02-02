# 使用指南

## ✅ 项目已创建完成

notification-test 项目已经创建完成，包含完整的 UVX 包结构。

## 📁 项目结构

```
notification-test/
├── pyproject.toml          # Python 包配置
├── README.md               # 项目说明
├── INSTALL.md             # 安装发布指南
├── USAGE.md               # 本文件
├── .env                   # 环境变量配置（已复制）
├── .env.example           # 环境变量示例
├── test_local.py          # 本地测试脚本
└── src/
    └── notification_mcp/
        ├── __init__.py    # 包初始化
        └── server.py      # MCP 服务器主代码
```

## 🎯 当前状态

✅ 项目结构已创建  
✅ 代码已从 notification_v3.py 迁移  
✅ 环境变量已复制  
✅ 本地测试通过（邮件发送成功）  

## 🚀 快速开始

### 1. 本地测试（已完成）

```bash
cd notification-test
python3 test_local.py
```

测试结果：
- ✅ 邮件发送成功
- ⚠️ 钉钉消息需要包含关键词

### 2. 本地开发模式安装

如果要在本地使用 `notification-mcp-server` 命令：

```bash
cd notification-test
pip install -e .
```

然后可以直接运行：
```bash
notification-mcp-server
```

### 3. 构建包（准备发布）

```bash
cd notification-test

# 安装构建工具
pip install build

# 构建包
python -m build
```

这会在 `dist/` 目录生成：
- `notification_mcp_server-1.0.0.tar.gz`
- `notification_mcp_server-1.0.0-py3-none-any.whl`

### 4. 本地测试 UVX 安装

```bash
# 从本地 wheel 文件安装测试
pip install dist/notification_mcp_server-1.0.0-py3-none-any.whl

# 运行
notification-mcp-server
```

### 5. 发布到 PyPI（可选）

如果要分享给其他人使用：

```bash
# 安装上传工具
pip install twine

# 检查包
twine check dist/*

# 上传到 PyPI（需要先注册账号）
twine upload dist/*
```

发布后，其他人可以通过以下方式使用：

```bash
# 使用 uvx 运行（推荐）
uvx notification-mcp-server@latest

# 或安装后使用
pip install notification-mcp-server
notification-mcp-server
```

## 🔧 在 Kiro IDE 中使用

### 方式 1：使用本地路径（当前推荐）

在 `.kiro/settings/mcp.json` 中：

```json
{
  "mcpServers": {
    "notification": {
      "command": "python3",
      "args": [
        "/Users/yongwei.shao/Documents/AI/AITools/notification-test/src/notification_mcp/server.py"
      ],
      "env": {
        "SMTP_SERVER": "smtp.163.com",
        "SMTP_PORT": "465",
        "EMAIL_ACCOUNT": "18168352057@163.com",
        "EMAIL_PASSWORD": "your-auth-code",
        "SMTP_SSL": "true",
        "DINGTALK_WEBHOOK": "your-webhook-url"
      },
      "disabled": false
    }
  }
}
```

### 方式 2：使用 UVX（发布后）

发布到 PyPI 后，可以使用：

```json
{
  "mcpServers": {
    "notification": {
      "command": "uvx",
      "args": ["notification-mcp-server@latest"],
      "env": {
        "SMTP_SERVER": "smtp.163.com",
        "SMTP_PORT": "465",
        "EMAIL_ACCOUNT": "18168352057@163.com",
        "EMAIL_PASSWORD": "your-auth-code",
        "SMTP_SSL": "true",
        "DINGTALK_WEBHOOK": "your-webhook-url"
      },
      "disabled": false
    }
  }
}
```

## 📊 对比：本地 vs UVX

### 本地方式（当前使用）
✅ 可以随时修改代码  
✅ 无需发布到 PyPI  
✅ 适合个人使用和开发  
❌ 需要指定完整路径  
❌ 不能分享给其他人  

### UVX 方式（发布后）
✅ 简单的配置  
✅ 自动版本管理  
✅ 可以分享给其他人  
✅ 自动更新到最新版本  
❌ 需要发布到 PyPI  
❌ 修改代码需要重新发布  

## 🎓 总结

1. **notification-test** 项目已创建完成，包含完整的 UVX 包结构
2. **本地测试通过**，邮件和钉钉功能正常
3. **可以选择**：
   - 继续使用本地路径方式（适合个人使用）
   - 发布到 PyPI 使用 UVX（适合分享）

## 📝 下一步

- 如果只是个人使用：保持当前的本地路径配置即可
- 如果要分享给其他人：按照 INSTALL.md 的步骤发布到 PyPI

@author shao
