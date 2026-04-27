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
- **多页面设计**：包含语音控制、PLC监控、3D模型、数据可视化、数据库管理、知识库和配置管理页面
- **数字漫游模式**：支持 3D 模型展示和实验室介绍

## 🎯 两种使用模式

本项目支持两种使用模式，请根据您的需求选择合适的模式：

### 模式一：无前端模式（推荐用于工业环境）

直接运行后端程序，通过外置麦克风和 PLC 内的触发变量进行语音交互，或通过控制台输入指令。适合工业现场部署，无需浏览器界面。

**特点**：
- 占用资源少，适合嵌入式或远程部署
- 响应速度快，无网络延迟
- 支持物理按键或 PLC 变量触发语音输入
- 控制台直接查看日志和状态

### 模式二：有前端模式（推荐用于开发和调试）

启动后端 API 服务和前端开发服务器，通过浏览器界面进行操作和控制。适合开发调试和需要可视化界面的场景。

**特点**：
- 现代化 Web 界面，操作友好
- 支持 3D 模型展示
- 实时数据可视化和历史记录
- 远程访问和控制

---

## 🛠️ 环境准备

### 硬件要求

**模式一（无前端模式）**：
- PLC 设备（Beckhoff TwinCAT3）
- 运行 Windows/Linux 的工控机或服务器
- 麦克风设备（支持 USB 或 3.5mm 接口）
- 网络连接（用于连接 LLM 和 ASR 服务）

**模式二（有前端模式）**：
- 以上全部硬件
- 开发或演示用的电脑/服务器
- 支持现代浏览器的客户端设备（Chrome、Firefox、Edge 等）

### 软件要求

- Python 3.8+
- Node.js 18+ 和 npm
- PLC 运行时环境（TwinCAT3）

---

## 📦 快速开始

### 模式一：无前端模式

#### 1. 安装后端依赖

```bash
# 进入项目根目录
cd voice_plc_controller

# 进入 backend 目录
cd backend

# 创建并激活conda虚拟环境（推荐）
conda create -n voice_plc python=3.8

# 激活虚拟环境
conda activate voice_plc

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac

# 编辑 .env 文件，配置必要的参数
notepad .env   # Windows
nano .env      # Linux/Mac
```

**关键配置项**：

```env
# ASR 配置 - 语音识别
ASR_PROVIDER=aliyun                    # ASR 提供商：aliyun 或 funasr
ASR_SAMPLE_RATE=16000                  # 采样率
ASR_TRIGGER_KEY=ctrl_r                 # 键盘触发快捷键

# 阿里云 ASR 配置（如果使用阿里云）
ALIYUN_ASR_APPKEY=your_appkey
ALIYUN_AK_ID=your_access_key_id
ALIYUN_AK_SECRET=your_access_key_secret
ALIYUN_ASR_URL=wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1

# TTS 配置 - 语音合成
TTS_PROVIDER=edge                      # TTS 提供商：edge
TTS_VOICE=zh-CN-XiaoxiaoNeural         # 语音角色
TTS_VOLUME=0.8                         # 音量 0.0-1.0

# LLM 配置 - 大语言模型
LLM_PROVIDER=openai                    # LLM 提供商
LLM_MODEL=gpt-4o-mini                   # 模型名称
LLM_API_KEY=your_api_key               # API Key
LLM_BASE_URL=https://api.openai.com/v1 # API 地址
LLM_TEMPERATURE=0.7                    # 温度参数
LLM_MAX_TOKENS=1024                    # 最大令牌数

# PLC 配置
PLC_ENABLED=true                       # 启用 PLC
PLC_PROVIDER=pyads                     # PLC 提供商
PLC_AMS_NET_ID=192.168.1.1.1.1         # PLC AMS Net ID
PLC_AMS_PORT=851                       # PLC AMS 端口
PLC_TRIGGER_VAR=MAIN.bVoiceTrigger     # 触发变量（PLC 变量触发录音）

# 模板匹配（快速响应常用指令）
USE_TEMPLATE_MATCHING=true

# 交互开关
VOICE_INPUT_ENABLED=true               # 语音输入
VOICE_OUTPUT_ENABLED=true              # 语音输出

# 日志
LOG_LEVEL=INFO
VERBOSE=true
```

#### 3. 运行程序

```bash
# 确保在 backend 目录下
cd backend

# 确保conda虚拟环境已激活
conda activate voice_plc

# 运行主程序
python app/main.py
```

#### 4. 使用方式

**启动后**，程序会显示以下信息：

```
按下 'ctrl_r' 键开始说话，松开结束。
📝 控制台输出已启用
💬 控制台已就绪，输入 '/' 查看命令，直接输入文字对话
```

**语音交互**：
- 按住触发键（如 `ctrl_r`）说话，松开后自动识别
- 或等待 PLC 触发变量变为 true 时自动开始录音

**控制台命令**：
- 直接输入文字按回车发送
- 输入 `/help` 查看所有可用命令
- 输入 `/voice status` 查看语音状态
- 输入 `/plc status` 查看 PLC 连接状态
- 输入 `/clear` 清空对话历史
- 输入 `/exit` 退出程序

---

### 模式二：有前端模式

#### 1. 安装后端依赖

```bash
# 进入项目根目录
cd voice_plc_controller

# 进入 backend 目录
cd backend

# 创建并激活conda虚拟环境（推荐）
conda create -n voice_plc python=3.8

# 激活虚拟环境
conda activate voice_plc

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置后端环境变量

```bash
# 复制环境变量模板
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac

# 编辑 .env 文件，配置 ASR、TTS、LLM 和 PLC 参数
notepad .env   # Windows
nano .env      # Linux/Mac
```

**关键配置项**（同上，请参考模式一的配置说明）

#### 3. 安装前端依赖

```bash
# 新开一个终端，进入 frontend 目录
cd voice_plc_controller/frontend

# 安装依赖
npm install
```

#### 4. 配置前端环境变量

```bash
# 复制环境变量模板
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac

# 编辑 .env 文件
notepad .env   # Windows
nano .env      # Linux/Mac
```

```env
# 后端API基础URL
VITE_API_BASE_URL=http://localhost:8000

# 前端应用配置
VITE_APP_TITLE=语音PLC控制
VITE_APP_VERSION=1.0.0
```

#### 5. 运行程序

**启动后端 API 服务**：

```bash
# 终端 1：进入 backend 目录
cd voice_plc_controller/backend

# 激活conda虚拟环境
conda activate voice_plc

# 运行 API 服务
python app/api.py
```

看到以下输出表示启动成功：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**启动前端开发服务器**：

```bash
# 终端 2：进入 frontend 目录
cd voice_plc_controller/frontend

# 运行开发服务器
npm run dev
```

看到以下输出表示启动成功：
```
VITE ready in xxx ms
➜ Local: http://localhost:5173/
```

#### 6. 访问界面

打开浏览器访问：`http://localhost:5173`

**功能页面说明**：

1. **语音控制页面**（首页）
   - 文本输入框输入指令
   - 麦克风按钮进行语音输入
   - 查看系统状态和响应

2. **PLC监控页面**
   - 查看 PLC 变量列表
   - 搜索和筛选变量
   - 编辑变量值
   - 隐藏/显示和锁定/解锁变量

3. **3D模型页面**
   - 查看 3D 模型
   - 模型旋转、缩放和平移

4. **数据可视化页面**
   - 查看数据图表
   - 分析数据趋势

5. **数据库管理页面**
   - 管理系统数据

6. **知识库页面**
   - 查看系统文档

7. **配置管理页面**
   - 查看和修改系统配置
   - 配置修改后请点击保存按钮使配置生效

8. **数字漫游模式**
   - 点击页面顶部的「数字漫游」按钮进入
   - 查看 3D 模型、数据监控、系统状态和实验室介绍

---

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
- **HTTP 客户端**：Axios
- **3D 渲染**：Three.js
- **数据可视化**：ECharts

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
│   │   ├── hdri/         # HDR 环境贴图
│   │   ├── models/       # 3D 模型文件
│   │   ├── favicon.ico   # 网站图标
│   │   └── lab.png       # 实验室图片
│   ├── src/              # 源代码目录
│   │   ├── api/          # API 调用封装
│   │   │   ├── index.ts  # API 接口定义
│   │   │   └── websocket.ts  # WebSocket 通信
│   │   ├── assets/       # 静态资源
│   │   │   ├── base.css  # 基础样式
│   │   │   ├── logo.jpg  # 项目 logo
│   │   │   └── main.css  # 全局样式
│   │   ├── config/       # 配置文件
│   │   │   ├── modelMappings.ts  # 模型映射
│   │   │   └── quickCommands.ts  # 快速命令
│   │   ├── router/       # 路由配置
│   │   │   └── index.ts  # 路由定义
│   │   ├── views/        # 页面视图
│   │   │   ├── AboutView.vue  # 关于页面
│   │   │   ├── ConfigView.vue  # 配置管理页面
│   │   │   ├── DataView.vue  # 数据可视化页面
│   │   │   ├── DatabaseView.vue  # 数据库管理页面
│   │   │   ├── DigitalRoamingView.vue  # 数字漫游页面
│   │   │   ├── HomeView.vue  # 语音控制页面
│   │   │   ├── KnowledgeView.vue  # 知识库页面
│   │   │   ├── ModelView.vue  # 3D 模型页面
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
├── videos/               # 演示视频
├── .gitignore            # Git 忽略配置
├── .gitattributes        # Git 属性配置
├── LICENSE               # 许可证文件
└── README.md             # 项目说明
```

## ⚙️ 配置说明

### 后端变量映射

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

### 前端模型映射

在 `frontend/src/config/modelMappings.ts` 中配置 3D 模型组件到 PLC 变量的映射：

```typescript
export interface ModelMapping {
  variable: string
  label: string
}

export const MODEL_COMPONENT_MAPPINGS: Record<string, ModelMapping> = {
  Mesh149: { variable: 'MAIN.WaterLevel', label: '水箱1水位' },
  Mesh153: { variable: 'MAIN.WaterLevel2', label: '水箱2水位' },
  Mesh185: { variable: 'MAIN.Temperature', label: '加热器温度' }
}
```

**说明**：
- `Mesh149`、`Mesh153`、`Mesh185` 等是 3D 模型中的组件名称
- `variable` 对应 PLC 中的变量名
- `label` 是显示在界面上的标签文本
- 配置后，前端会自动将 3D 模型组件与 PLC 变量关联，实现数据可视化

### 监控变量（有前端模式启用）

在 `backend/.env` 文件中配置要监控的变量：

```env
# 有前端模式启用
MONITOR_VARIABLES=MAIN.WaterLevel:REAL, MAIN.Temperature:REAL
MONITOR_INTERVAL_MS=200
```

### 数据库配置（有前端模式启用）

在 `backend/.env` 文件中配置数据库：

```env
# 有前端模式启用
DB_ENABLED=true
DB_TYPE=sqlite
SQLITE_DB_PATH=plc_data.db
```

### 数据采集配置（有前端模式启用）

在 `backend/.env` 文件中配置数据采集：

```env
# 有前端模式启用
DATA_COLLECTION_ENABLED=true
DATA_COLLECTION_INTERVAL=1000
DATA_COLLECTION_BATCH_SIZE=10
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
- 检查端口是否被占用（默认 8000）
- 确保依赖包已正确安装
- 查看后端日志输出

### 前端开发问题
- 运行 `npm install` 确保依赖安装完整
- 检查 `vite.config.ts` 配置是否正确
- 确保后端 API 服务正在运行
- 检查浏览器控制台错误信息

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

**注意**：由于测试难以全面覆盖，可能存在潜在的 bug，欢迎通过 GitHub Issues 反馈。