import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # ASR 通用配置
    ASR_PROVIDER = os.getenv("ASR_PROVIDER", "funasr")  # funasr / aliyun
    ASR_SAMPLE_RATE = int(os.getenv("ASR_SAMPLE_RATE", "16000"))
    ASR_TRIGGER_KEY = os.getenv("ASR_TRIGGER_KEY", "ctrl_r")

    # FunASR 配置
    ASR_MODEL = os.getenv("ASR_MODEL", "paraformer-zh-streaming")
    ASR_DEVICE = os.getenv("ASR_DEVICE", "cpu")
    # FunASR 流式参数
    ASR_CHUNK_SIZE_STR = os.getenv("ASR_CHUNK_SIZE", "0,10,5")
    ASR_ENCODER_CHUNK_LOOK_BACK = int(os.getenv("ASR_ENCODER_CHUNK_LOOK_BACK", "4"))
    ASR_DECODER_CHUNK_LOOK_BACK = int(os.getenv("ASR_DECODER_CHUNK_LOOK_BACK", "1"))

    # 阿里云 ASR 配置
    ALIYUN_ASR_APPKEY = os.getenv("ALIYUN_ASR_APPKEY", "")
    ALIYUN_AK_ID = os.getenv("ALIYUN_AK_ID", "")
    ALIYUN_AK_SECRET = os.getenv("ALIYUN_AK_SECRET", "")
    ALIYUN_ASR_URL = os.getenv("ALIYUN_ASR_URL", "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1")
    ALIYUN_ASR_REGION = os.getenv("ALIYUN_ASR_REGION", "cn-shanghai")
    # 兼容旧版 Token 直接配置
    ALIYUN_ASR_TOKEN = os.getenv("ALIYUN_ASR_TOKEN", "")

    @property
    def asr_chunk_size(self) -> list:
        """解析逗号分隔的 chunk_size 字符串为整数列表"""
        return [int(x.strip()) for x in self.ASR_CHUNK_SIZE_STR.split(",") if x.strip()]

    # TTS
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")
    TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")
    TTS_VOLUME = float(os.getenv("TTS_VOLUME", "0.8"))
    TTS_PLAYER = os.getenv("TTS_PLAYER", "pygame")   # pygame / system

    # LLM
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    # PLC
    PLC_ENABLED = os.getenv("PLC_ENABLED", "false").lower() == "true"
    PLC_PROVIDER = os.getenv("PLC_PROVIDER", "mock")
    PLC_AMS_NET_ID = os.getenv("PLC_AMS_NET_ID", "192.168.1.1.1.1")
    PLC_AMS_PORT = int(os.getenv("PLC_AMS_PORT", "851"))
    PLC_IP_ADDRESS = os.getenv("PLC_IP_ADDRESS", None)
    PLC_TRIGGER_VAR = os.getenv("PLC_TRIGGER_VAR", None)

    # 日志
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", None)
    VERBOSE = os.getenv("VERBOSE", "true").lower() == "true"

    # 音频
    AUDIO_CHUNK = 1024
    AUDIO_FORMAT = 8  # pyaudio.paInt16

    # 模板匹配开关
    USE_TEMPLATE_MATCHING = os.getenv("USE_TEMPLATE_MATCHING", "true").lower() == "true"

    # 默认监控变量
    MONITOR_VARIABLES_STR = os.getenv("MONITOR_VARIABLES", "")
    MONITOR_INTERVAL_MS = int(os.getenv("MONITOR_INTERVAL_MS", "200"))

    # 交互模式开关
    VOICE_INPUT_ENABLED = os.getenv("VOICE_INPUT_ENABLED", "true").lower() == "true"
    VOICE_OUTPUT_ENABLED = os.getenv("VOICE_OUTPUT_ENABLED", "true").lower() == "true"
    CONSOLE_INPUT_ENABLED = os.getenv("CONSOLE_INPUT_ENABLED", "false").lower() == "true"
    CONSOLE_OUTPUT_ENABLED = os.getenv("CONSOLE_OUTPUT_ENABLED", "false").lower() == "true"

    # 物理名称映射配置文件路径
    MAPPINGS_FILE = Path(__file__).parent / "variable_mappings.yaml"

    @property
    def mappings(self) -> dict:
        if not self.MAPPINGS_FILE.exists():
            return {}
        with open(self.MAPPINGS_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('mappings', {})

    @property
    def monitor_variables(self):
        if not self.MONITOR_VARIABLES_STR:
            return []
        vars_list = []
        for item in self.MONITOR_VARIABLES_STR.split(','):
            if ':' in item:
                name, vtype = item.strip().split(':')
                vars_list.append((name.strip(), vtype.strip().upper()))
        return vars_list

settings = Settings()