# Shai - AI 驱动的 Shell 命令生成器

[English](#english-version) | [中文](#中文版)

## 中文版

### 📖 项目简介

Shai 是一个 Shell 命令生成工具，利用大型语言模型（LLM）根据自然语言描述自动生成相应的 Shell 命令，提供安全的风险评估和交互式确认机制。

### ✨ 核心特性

- 🤖 **智能命令生成** - 基于自然语言描述生成准确的 Shell 命令
- 🔒 **安全评估** - 自动评估命令风险等级（安全/警告/危险）
- ⚙️ **灵活配置** - 支持多样模型配置
- 🎨 **交互式界面** - 彩色输出和加载动画，提升用户体验

### 🚀 快速开始

#### 安装方法

```bash
uv tool install shai-python
```

#### 基本使用

**命令行模式：**
```bash
shai 列出当前目录下的所有 Python 文件
```

**交互式模式：**
```bash
shai
>> 查找大于 10MB 的文件
```

**配置编辑：**
```bash
shai config
```

### ⚙️ 配置说明

#### 首次运行配置

首次运行时会自动创建配置文件，你需要配置 API 密钥：

#### 配置文件位置

- **配置文件**: `~/.config/shai/config.yaml`

#### 配置示例

```yaml
# ~/.config/shai/config.yaml

# 调用模型
default_model: "deepseek" # Point to ID in models

# 提供商配置
providers:
  deepseek:
    api_key: "${DEEPSEEK_API_KEY}" # refer to environment variable
    #base_url: "https://api.deepseek.com"  # 使用缺省
  智普:
    api_key: "sk-..." # 建议使用环境变量，比如 ${GLM_API_KEY}
    base_url: "https://open.bigmodel.cn/api/paas/v4"
  火山方舟:
    api_key: "${VOLCANO_API_KEY}"
    base_url: "https://ark.cn-beijing.volces.com/api/v3"
  openai:
    api_key: "${OPENAI_API_KEY}" 
  google:
    api_key: "${GOOGLE_API_KEY}" 
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
  xai:
    api_key: "${XAI_API_KEY}" 
  openrouter:
    api_key: "${OPENROUTER_API_KEY}" 

# 模型配置
models:
  - id: "deepseek-chat"
    provider: "deepseek"
    alias: "deepseek"

  - id: "glm-4.7-flash"
    provider: "智普"

  - id: "doubao-seed-1-6-flash-250828"
    provider: "火山方舟"
    alias: "doubao-flash"
```

### 🔧 功能详解

#### 命令生成流程

1. **输入描述** - 用户输入自然语言任务描述
2. **AI 分析** - 模型分析任务并生成合适的命令
3. **风险评估** - 自动评估命令的风险等级
4. **用户确认** - 根据风险等级提示用户确认执行
5. **命令执行** - 用户确认后执行生成的命令

#### 风险等级

- 🟢 **安全 (Safe)** - 无害命令，可直接执行
- 🟡 **警告 (Caution)** - 可能有副作用，需要确认
- 🔴 **危险 (Danger)** - 高风险命令，需要明确确认


### 🐛 故障排除

#### 常见问题

**Q: API 密钥配置错误**
A: 运行 `shai config` 重新配置，或设置环境变量

**Q: 命令执行失败**
A: 检查网络连接和 API 配额，确认配置正确

**Q: 权限错误**
A: 配置文件会自动创建在当前用户目录，无需特殊权限

### 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**安全提示**: 使用 AI 生成的命令时请谨慎，特别是涉及系统修改或数据删除的操作。建议在非生产环境中先测试命令效果。

## English Version

### 📖 Project Introduction

Shai uses large language models (LLMs) to generate shell command based on natural language descriptions. It provides safety risk assessment, interactive confirmation mechanisms.

### ✨ Core Features

- 🤖 **Intelligent Command Generation** - Generate accurate shell commands from natural language descriptions
- 🔒 **Safety Assessment** - Automatic risk level evaluation (Safe/Caution/Danger)
- ⚙️ **Flexible Configuration** - Various models configuration
- 🎨 **Interactive Interface** - Colored output and loading animations for better user experience

### 🚀 Quick Start

#### Installation

```bash
uv tool install shai-python
```

#### Basic Usage

**Command Line Mode:**
```bash
shai list all Python files in current directory
```

**Interactive Mode:**
```bash
shai
>> find files larger than 10MB
```

**Configuration Editing:**
```bash
shai config
```

### ⚙️ Configuration

#### First Run Setup

Configuration file is automatically created on first run:


#### Configuration File Location

- **Config File**: `~/.config/shai/config.yaml`

#### Configuration Example

```yaml
# ~/.config/shai/config.yaml

# Default settings
default_model: "deepseek" # Point to ID or alias in models

# Providers
providers:
  deepseek:
    api_key: "${DEEPSEEK_API_KEY}" # refer to environment variable
    #base_url: "https://api.deepseek.com"  # use default base_url
  openai:
    api_key: "sk..."  # recommended NOT to use plain text API KEY.
  google:
    api_key: "${GOOGLE_API_KEY}" 
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
  xai:
    api_key: "${XAI_API_KEY}" 
  openrouter:
    api_key: "${OPENROUTER_API_KEY}" 

# Models
models:
  - id: "deepseek-chat"
    provider: "deepseek"
    alias: "deepseek"

```

### 🔧 Features

#### Command Generation Process

1. **Input Description** - User provides natural language task description
2. **AI Analysis** - Model analyzes task and generates appropriate command
3. **Risk Assessment** - Automatic risk level evaluation
4. **User Confirmation** - Prompt user based on risk level
5. **Command Execution** - Execute generated command after confirmation

#### Risk Levels

- 🟢 **Safe** - Harmless commands, can be executed directly
- 🟡 **Caution** - Commands with potential side effects, require confirmation
- 🔴 **Danger** - High-risk commands, require explicit confirmation

### 🐛 Troubleshooting

#### Common Issues

**Q: API Key Configuration Error**
A: Run `shai config` to reconfigure, or set environment variables

**Q: Command Execution Failed**
A: Check network connection and API quota, verify configuration

**Q: Module Not Found Error**
A: Ensure installing `shai-python` package, not `shai`

**Q: Permission Error**
A: Configuration files are created in user directory, no special permissions needed


### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Security Notice**: Use AI-generated commands with caution, especially those involving system modifications or data deletion. Test command effects in non-production environments first.