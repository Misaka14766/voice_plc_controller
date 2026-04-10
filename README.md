# Voice PLC Controller

一个基于语音识别和大语言模型的 PLC 控制器，支持通过语音指令控制工业设备。

## 功能特点

- **语音交互**：通过语音指令控制 PLC 设备
- **多平台支持**：兼容 Windows、Linux 和 macOS
- **模块化设计**：支持多种 ASR、TTS 和 LLM 提供商
- **实时监控**：实时监控 PLC 变量状态
- **模板匹配**：快速响应常用指令，减少 LLM 调用
- **控制台交互**：支持命令行交互模式
- **PLC 触发**：支持通过 PLC 变量触发语音输入

## 技术栈

- **前端**：Python 3.8+
- **语音识别**：FunASR
- **语音合成**：Edge TTS
- **大语言模型**：OpenAI 兼容 API（如 DeepSeek）
- **PLC 通信**：pyads（Beckhoff PLC）
- **工具库**：pyaudio、pynput

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 文件为 `.env` 并填写相关配置：

```env
# ASR 配置
ASR_PROVIDER=funasr
ASR_MODEL=paraformer-zh-streaming
ASR_DEVICE=cpu

# TTS 配置
TTS_PROVIDER=edge
TTS_VOICE=zh-CN-XiaoxiaoNeural
TTS_VOLUME=0.8

# LLM 配置
LLM_PROVIDER=openai
LLM_MODEL=deepseek-chat
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com/v1

# PLC 配置
PLC_ENABLED=false
PLC_PROVIDER=mock
PLC_AMS_NET_ID=192.168.1.1.1.1
PLC_AMS_PORT=851
PLC_IP_ADDRESS=192.168.1.100

# 其他配置
TRIGGER_KEY=ctrl_r
LOG_LEVEL=INFO
```

### 3. 运行程序

```bash
python app/main.py
```

## 使用方法

### 语音控制

1. 按下配置的触发键（默认 `Ctrl+R`）开始说话
2. 说出控制指令，例如：
   - "启动电机"
   - "设置温度为 25 度"
   - "查看当前压力"
3. 松开触发键，系统会识别并执行指令

### 控制台命令

输入 `/help` 查看可用命令：

- `/voice input on/off` - 开启/关闭语音输入
- `/voice output on/off` - 开启/关闭语音输出
- `/voice status` - 查看当前语音状态
- `/volume [0.0-1.0]` - 设置或查看音量
- `/stop` - 停止当前播放
- `/plc status` - 查看 PLC 连接状态
- `/clear` - 清空对话历史
- `/exit` 或 `/quit` - 退出程序

## 目录结构

```
voice_plc_controller/
├── app/                  # 应用主目录
│   ├── __init__.py
│   └── main.py           # 主程序入口
├── config/               # 配置目录
│   ├── __init__.py
│   ├── settings.py       # 配置管理
│   └── variable_mappings.yaml  # 变量映射配置
├── core/                 # 核心功能模块
│   ├── asr/              # 语音识别
│   ├── llm/              # 大语言模型
│   ├── plc/              # PLC 通信
│   ├── tts/              # 语音合成
│   ├── __init__.py
│   ├── factory.py        # 工厂模式
│   └── template_matcher.py  # 模板匹配
├── utils/                # 工具类
│   ├── __init__.py
│   ├── audio_recorder.py # 音频录制
│   ├── key_trigger.py    # 按键触发
│   └── logger.py         # 日志工具
├── .env                  # 环境变量配置
├── README.md             # 项目说明
└── requirements.txt      # 依赖包
```

## 配置说明

### 变量映射

在 `config/variable_mappings.yaml` 中配置物理名称到 PLC 变量的映射：

```yaml
mappings:
  电机1:
    variable: MAIN.Motor1
    type: BOOL
    description: 主电机
  温度传感器:
    variable: MAIN.Temperature
    type: REAL
    description: 温度传感器值
  压力传感器:
    variable: MAIN.Pressure
    type: REAL
    description: 压力传感器值
```

### 监控变量

在 `.env` 文件中配置要监控的变量：

```env
MONITOR_VARIABLES=MAIN.Temperature:REAL,MAIN.Pressure:REAL,MAIN.Motor1:BOOL
MONITOR_INTERVAL_MS=200
```

## 扩展与定制

### 添加新的 ASR 提供商

在 `core/asr/` 目录下创建新的 ASR 实现类，继承 `BaseASR` 并实现相关方法。

### 添加新的 TTS 提供商

在 `core/tts/` 目录下创建新的 TTS 实现类，继承 `BaseTTS` 并实现相关方法。

### 添加新的 LLM 提供商

在 `core/llm/` 目录下创建新的 LLM 实现类，继承 `BaseLLM` 并实现相关方法。

### 添加新的 PLC 提供商

在 `core/plc/` 目录下创建新的 PLC 实现类，继承 `BasePLC` 并实现相关方法。

## 故障排除

### 语音识别问题
- 确保麦克风正常工作
- 检查 ASR 模型是否正确安装
- 调整环境噪音

### PLC 连接问题
- 检查网络连接
- 验证 AMS Net ID 和端口配置
- 确保 PLC 程序正在运行

### 语音合成问题
- 检查网络连接（Edge TTS 需要网络）
- 验证 TTS 语音配置是否正确

## 贡献指南

1. Fork 本仓库
2. 创建 feature 分支
3. 提交代码
4. 发起 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请通过 GitHub Issues 提交。
