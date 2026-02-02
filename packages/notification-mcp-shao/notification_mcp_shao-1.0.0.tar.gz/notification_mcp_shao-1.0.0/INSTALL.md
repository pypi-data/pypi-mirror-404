# 安装和使用指南

## 📦 项目结构

```
notification-test/
├── pyproject.toml          # 包配置文件
├── README.md               # 项目说明
├── INSTALL.md             # 本文件
├── .env.example           # 环境变量示例
├── test_local.py          # 本地测试脚本
└── src/
    └── notification_mcp/
        ├── __init__.py
        └── server.py      # 主服务器代码
```

## 🔧 开发和测试流程

### 1. 复制环境变量配置

```bash
cd notification-test
cp .env.example .env
```

然后编辑 `.env` 文件，填入你的实际配置。

### 2. 安装依赖（开发模式）

```bash
# 使用 pip 安装开发模式
pip install -e .

# 或使用 uv
uv pip install -e .
```

### 3. 本地测试

```bash
# 测试邮件和钉钉功能
python test_local.py
```

### 4. 测试 MCP 服务器

创建测试脚本 `test_mcp.py`：

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "notification_mcp.server"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"可用工具: {[t.name for t in tools.tools]}")

asyncio.run(test())
```

## 📤 发布到 PyPI

### 1. 安装构建工具

```bash
pip install build twine
```

### 2. 构建包

```bash
python -m build
```

这会在 `dist/` 目录生成：
- `notification_mcp_server-1.0.0.tar.gz` (源码包)
- `notification_mcp_server-1.0.0-py3-none-any.whl` (wheel包)

### 3. 检查包

```bash
twine check dist/*
```

### 4. 上传到 TestPyPI（测试）

```bash
# 首先注册 TestPyPI 账号: https://test.pypi.org/account/register/
twine upload --repository testpypi dist/*
```

### 5. 测试安装

```bash
# 从 TestPyPI 安装
uvx --index-url https://test.pypi.org/simple/ notification-mcp-server@latest

# 或使用 pip
pip install --index-url https://test.pypi.org/simple/ notification-mcp-server
```

### 6. 上传到正式 PyPI

```bash
# 注册 PyPI 账号: https://pypi.org/account/register/
twine upload dist/*
```

### 7. 正式使用

```bash
# 使用 uvx 运行
uvx notification-mcp-server@latest

# 或安装后使用
pip install notification-mcp-server
notification-mcp-server
```

## 🎯 在 Kiro IDE 中配置

发布后，在 `.kiro/settings/mcp.json` 中配置：

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
        "DINGTALK_WEBHOOK": "your-webhook-url",
        "DINGTALK_SECRET": ""
      },
      "disabled": false
    }
  }
}
```

## 🔄 更新版本

1. 修改 `pyproject.toml` 中的 `version`
2. 修改 `src/notification_mcp/__init__.py` 中的 `__version__`
3. 重新构建和上传

```bash
python -m build
twine upload dist/*
```

## 📝 注意事项

- ✅ 包名使用连字符：`notification-mcp-server`
- ✅ 模块名使用下划线：`notification_mcp`
- ✅ 命令行工具名：`notification-mcp-server`
- ✅ 环境变量通过 `env` 字段传递
- ✅ 日志保存在 `/tmp/mcp_notification_server.log`

## 🐛 故障排查

### 查看日志
```bash
tail -f /tmp/mcp_notification_server.log
```

### 测试环境变量
```bash
SMTP_SERVER=smtp.163.com \
EMAIL_ACCOUNT=test@163.com \
uvx notification-mcp-server@latest
```

### 重新安装
```bash
uvx --reinstall notification-mcp-server@latest
```
