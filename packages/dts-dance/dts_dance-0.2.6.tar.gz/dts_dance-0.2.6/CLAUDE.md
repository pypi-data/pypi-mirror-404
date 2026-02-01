# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在该代码仓库中工作时提供指导。

## 项目概述

dts-dance 是一个 ByteDTS 监控和指标分析工具，构建为 Python 包。它提供了用于与各种字节跳动内部服务交互的客户端库，包括 DFlow、飞书（Lark）、SpaceX 通知、指标服务和云服务。

## 开发命令

### 环境设置

使用 pyenv + pip：
```bash
pyenv shell 3.12.10
python -m venv .venv
source .venv/bin/activate
pip install .
```

使用 uv（推荐）：
```bash
uv sync
source .venv/bin/activate
uv pip install .
uv run python xxx.py
```

### 构建和发布

构建包：
```bash
uv build
```

发布到 PyPI：
```bash
export UV_PUBLISH_TOKEN=pypi-xxx
uv publish
```

## 代码架构

### 包结构

主包是 `dtsdance/`，包含用于各种字节跳动内部服务的客户端模块：

- `feishu_base.py`: 飞书 API 认证基类，使用线程锁实现自动 token 续期管理
- `feishu_table.py`: 飞书多维表格（Bitable）操作 - 依赖 FeishuBase 进行认证
- `dflow.py`: DFlow 任务管理客户端 - 依赖 ByteCloudHelper 进行 JWT 认证
- `spacex.py`: SpaceX 通知服务，用于发送飞书消息 - 依赖 ByteCloudHelper
- `bytecloud.py`: ByteCloud JWT token 管理辅助类
- `metrics_fe.py`: Metrics 前端客户端
- `s3.py`: S3 存储操作
- `dsyncer.py`: DSyncer 客户端

### 关键依赖关系

- **FeishuBase → FeishuTable**: FeishuTable 需要 FeishuBase 实例进行认证
- **ByteCloudHelper → DFlowHelper**: DFlowHelper 需要 ByteCloudHelper 获取 JWT tokens
- **ByteCloudHelper → SpaceXNotifier**: SpaceXNotifier 需要 ByteCloudHelper 进行认证

### 认证模式

1. **飞书服务**: 使用 tenant_access_token，支持自动续期（提前 5 分钟刷新）
2. **ByteCloud 服务**: 使用通过 ByteCloudHelper 获取的 JWT tokens
3. **线程安全**: Token 管理使用 threading.Lock 防止竞态条件

### API 请求模式

所有客户端模块遵循相似的模式：
- 使用 requests 库进行 HTTP 操作
- 使用 loguru 进行集中式错误处理和日志记录
- 返回带类型提示的字典
- 失败时抛出异常供调用方处理

## 开发指南

- 需要 Python 3.12+
- 统一使用类型提示（dict[str, Any], Optional[str] 等）
- 行长度：150 字符（在 pyproject.toml 中配置）
- 使用 loguru 进行日志记录，不使用 print 语句（除非是遗留代码）
- 遵循现有的错误处理模式：记录警告并抛出异常
