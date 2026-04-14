# Voice PLC Controller

一个基于语音识别和大语言模型的 PLC 控制器，支持通过语音指令控制工业设备，包含完整的前后端实现。

## 🚀 功能特点

- **语音交互**：通过语音指令控制 PLC 设备
- **多平台支持**：兼容 Windows、Linux 和 macOS
- **模块化设计**：支持多种 ASR、TTS 和 LLM 提供商
- **实时监控**：实时监控 PLC 变量状态，支持变量读写操作
- **模板匹配**：快速响应常用指令，减少 LLM 调用
- **控制台交互**：支持命令行交互模式
- **PLC 触发**：支持通过 PLC 变量触发语音输入
- **RESTful API**：提供 HTTP 接口，支持与其他系统集成
- **现代化前端**：基于 Vue 3 + TypeScript + Element Plus 的响应式界面
- **多页面设计**：包含语音控制、PLC监控、配置管理和关于页面

## 🛠️ 技术栈

### 后端
- **语言**：Python 3.8+
- **Web 框架**：FastAPI
- **语音识别**：FunASR、阿里云 ASR
- **语音合成**：Edge TTS
- **大语言模型**：OpenAI 兼容 API（如 DeepSeek）
- **PLC 通信**：pyads（Beckhoff PLC）
- **工具库**：pyaudio、pynput、pygame

### 前端
- **框架**：Vue 3 + TypeScript
- **UI 库**：Element Plus
- **构建工具**：Vite
- **路由**：Vue Router
- **状态管理**：Pinia
- **HTTP 客户端**：Axios

## 📦 快速开始

### 1. 安装后端依赖

```bash
# 进入 backend 目录
cd backend

# 安装依赖
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
# 进入 frontend 目录
cd frontend

# 安装依赖
npm install
```

### 3. 配置环境变量

#### 后端环境变量

复制 `backend/.env.example` 文件为 `backend/.env` 并填写相关配置：

```env
# ASR 配置
ASR_PROVIDER=aliyun
ASR_SAMPLE_RATE=16000
ASR_TRIGGER_KEY=ctrl_r

# 阿里云 ASR 配置
ALIYUN_ASR_APPKEY=your_appkey
ALIYUN_AK_ID=your_access_key_id
ALIYUN_AK_SECRET=your_access_key_secret
ALIYUN_ASR_URL=wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1

# TTS 配置
TTS_PROVIDER=edge
TTS_VOICE=zh-CN-XiaoxiaoNeural
TTS_VOLUME=0.8
TTS_PLAYER=pygame

# LLM 配置
LLM_PROVIDER=openai
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024

# ARK 配置（示例）
#LLM_MODEL=doubao-1-5-pro-32k-250115
#LLM_API_KEY=your_api_key
#LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# PLC 配置
PLC_ENABLED=false
PLC_PROVIDER=mock
PLC_AMS_NET_ID=192.168.1.1.1.1
PLC_AMS_PORT=851
PLC_TRIGGER_VAR=MAIN.bVoiceTrigger

# 模板匹配
USE_TEMPLATE_MATCHING=true

# 交互开关
VOICE_INPUT_ENABLED=true
VOICE_OUTPUT_ENABLED=true

# 日志
LOG_LEVEL=INFO
VERBOSE=true

# 监控变量（可选）
# MONITOR_VARIABLES=MAIN.Temperature:REAL,MAIN.Pressure:REAL,MAIN.Motor1:BOOL
# MONITOR_INTERVAL_MS=200
```

#### 前端环境变量

复制 `frontend/.env.example` 文件为 `frontend/.env` 并填写相关配置：

```env
# 后端API基础URL
VITE_API_BASE_URL=http://localhost:8000

# 前端应用配置
VITE_APP_TITLE=语音PLC控制
VITE_APP_VERSION=1.0.0
```

### 4. 运行程序

#### 后端 API 服务

```bash
# 进入 backend 目录
cd backend

# 运行 API 服务
python app/api.py
```

#### 前端开发服务器

```bash
# 进入 frontend 目录
cd frontend

# 运行开发服务器
npm run dev
```

## 🎯 使用方法

### 前端界面使用

1. **语音控制页面**：
   - 通过文本输入框输入指令
   - 点击麦克风按钮进行语音输入
   - 查看系统状态和响应

2. **PLC监控页面**：
   - 查看 PLC 变量列表
   - 搜索和筛选变量
   - 编辑变量值
   - 实时刷新变量状态

3. **配置管理页面**：
   - 查看系统配置
   - 查看连接状态
   - 查看系统信息

4. **关于页面**：
   - 查看项目信息
   - 了解核心功能
   - 查看技术栈

### API 接口

运行 API 服务后，可以通过以下接口与系统交互：

- `POST /api/chat` - 发送文本指令
- `POST /api/plc/read` - 读取 PLC 变量
- `POST /api/plc/write` - 写入 PLC 变量
- `GET /api/plc/variables` - 获取 PLC 变量列表
- `POST /api/tts` - 文本转语音
- `GET /api/health` - 健康检查
- `GET /api/status` - 获取系统状态
- `POST /api/clear` - 清空对话历史
- `GET /api/history` - 获取对话历史
- `GET /api/config` - 获取系统配置
- `WebSocket /ws/asr` - 语音识别WebSocket接口

## 📁 目录结构

```
voice_plc_controller/
├── backend/              # 后端应用
│   ├── app/              # 应用主目录
│   │   ├── __init__.py
│   │   ├── api.py        # API 服务
│   │   └── main.py       # 主程序入口
│   ├── config/           # 配置目录
│   │   ├── __init__.py
│   │   ├── settings.py   # 配置管理
│   │   └── variable_mappings.yaml  # 变量映射配置
│   ├── core/             # 核心功能模块
│   │   ├── asr/          # 语音识别
│   │   │   ├── aliyun_asr.py  # 阿里云 ASR
│   │   │   ├── funasr_asr.py  # FunASR
│   │   │   └── base.py   # ASR 基类
│   │   ├── llm/          # 大语言模型
│   │   ├── plc/          # PLC 通信
│   │   ├── tts/          # 语音合成
│   │   │   ├── players/  # 音频播放器
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── factory.py
│   │   │   │   ├── pygame_player.py
│   │   │   │   └── system_player.py
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── edge_tts.py  # Edge TTS
│   │   ├── __init__.py
│   │   ├── factory.py    # 工厂模式
│   │   └── template_matcher.py  # 模板匹配
│   ├── utils/            # 工具类
│   │   ├── __init__.py
│   │   ├── audio_recorder.py  # 音频录制
│   │   ├── key_trigger.py     # 按键触发
│   │   └── logger.py          # 日志工具
│   ├── .env              # 环境变量配置
│   ├── .env.example      # 环境变量模板
│   ├── __init__.py
│   └── requirements.txt  # 依赖包
├── frontend/             # 前端应用
│   ├── public/           # 公共静态资源
│   │   └── favicon.ico   # 网站图标
│   ├── src/              # 源代码目录
│   │   ├── api/          # API 调用封装
│   │   │   ├── index.ts  # API 接口定义
│   │   │   └── websocket.ts  # WebSocket 通信
│   │   ├── assets/       # 静态资源
│   │   │   ├── base.css  # 基础样式
│   │   │   ├── logo.svg  # 项目 logo
│   │   │   └── main.css  # 全局样式
│   │   ├── components/   # 组件
│   │   │   └── PlcPanel.vue  # PLC 控制面板
│   │   ├── router/       # 路由配置
│   │   │   └── index.ts  # 路由定义
│   │   ├── views/        # 页面视图
│   │   │   ├── AboutView.vue  # 关于页面
│   │   │   ├── ConfigView.vue  # 配置管理页面
│   │   │   ├── HomeView.vue  # 语音控制页面
│   │   │   └── PlcMonitorView.vue  # PLC 监控页面
│   │   ├── App.vue       # 应用根组件
│   │   └── main.ts       # 应用入口
│   ├── .env              # 环境变量配置
│   ├── .env.example      # 环境变量模板
│   ├── index.html        # HTML 入口
│   ├── package.json      # 前端项目配置
│   ├── package-lock.json # 依赖版本锁定
│   ├── tsconfig.json     # TypeScript 配置
│   └── vite.config.ts    # Vite 配置
├── .gitignore            # Git 忽略配置
├── .gitattributes        # Git 属性配置
├── LICENSE               # 许可证文件
└── README.md             # 项目说明
```

## ⚙️ 配置说明

### 变量映射

在 `backend/config/variable_mappings.yaml` 中配置物理名称到 PLC 变量的映射：

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

在 `backend/.env` 文件中配置要监控的变量：

```env
MONITOR_VARIABLES=MAIN.Temperature:REAL,MAIN.Pressure:REAL,MAIN.Motor1:BOOL
MONITOR_INTERVAL_MS=200
```

### 阿里云 ASR 配置

使用阿里云 ASR 时，需要配置以下参数：

```env
ASR_PROVIDER=aliyun
ALIYUN_ASR_APPKEY=your_appkey
ALIYUN_AK_ID=your_access_key_id
ALIYUN_AK_SECRET=your_access_key_secret
ALIYUN_ASR_URL=wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1
```

## 🔧 扩展与定制

### 添加新的 ASR 提供商

在 `backend/core/asr/` 目录下创建新的 ASR 实现类，继承 `BaseASR` 并实现相关方法。

### 添加新的 TTS 提供商

在 `backend/core/tts/` 目录下创建新的 TTS 实现类，继承 `BaseTTS` 并实现相关方法。

### 添加新的 LLM 提供商

在 `backend/core/llm/` 目录下创建新的 LLM 实现类，继承 `BaseLLM` 并实现相关方法。

### 添加新的 PLC 提供商

在 `backend/core/plc/` 目录下创建新的 PLC 实现类，继承 `BasePLC` 并实现相关方法。

### 添加新的音频播放器

在 `backend/core/tts/players/` 目录下创建新的播放器实现类，继承 `BasePlayer` 并实现相关方法。

## 🐛 故障排除

### 语音识别问题
- 确保麦克风正常工作
- 检查 ASR 配置是否正确
- 调整环境噪音
- 对于阿里云 ASR，确保网络连接正常且配置了正确的密钥

### PLC 连接问题
- 检查网络连接
- 验证 AMS Net ID 和端口配置
- 确保 PLC 程序正在运行

### 语音合成问题
- 检查网络连接（Edge TTS 需要网络）
- 验证 TTS 语音配置是否正确

### API 服务问题
- 检查端口是否被占用
- 确保依赖包已正确安装

## 🤝 贡献指南

1. Fork 本仓库
2. 创建 feature 分支
3. 提交代码
4. 发起 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

如有问题或建议，请通过 GitHub Issues 提交。

---

**注意**：本项目前端功能尚未完成。
