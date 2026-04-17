import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).parent.parent
ENV_FILE = BACKEND_ROOT / '.env'
load_dotenv(dotenv_path=ENV_FILE)

if not os.getenv('ASR_PROVIDER'):
    print(f"警告: 未找到.env文件或环境变量未设置，使用默认值")
    print(f"尝试加载的.env文件路径: {ENV_FILE}")

class Settings:
    ASR_PROVIDER = os.getenv("ASR_PROVIDER", "funasr")
    ASR_SAMPLE_RATE = int(os.getenv("ASR_SAMPLE_RATE", "16000"))
    ASR_TRIGGER_KEY = os.getenv("ASR_TRIGGER_KEY", "ctrl_r")

    ASR_MODEL = os.getenv("ASR_MODEL", "paraformer-zh-streaming")
    ASR_DEVICE = os.getenv("ASR_DEVICE", "cpu")
    ASR_CHUNK_SIZE_STR = os.getenv("ASR_CHUNK_SIZE", "0,10,5")
    ASR_ENCODER_CHUNK_LOOK_BACK = int(os.getenv("ASR_ENCODER_CHUNK_LOOK_BACK", "4"))
    ASR_DECODER_CHUNK_LOOK_BACK = int(os.getenv("ASR_DECODER_CHUNK_LOOK_BACK", "1"))

    ALIYUN_ASR_APPKEY = os.getenv("ALIYUN_ASR_APPKEY", "")
    ALIYUN_AK_ID = os.getenv("ALIYUN_AK_ID", "")
    ALIYUN_AK_SECRET = os.getenv("ALIYUN_AK_SECRET", "")
    ALIYUN_ASR_URL = os.getenv("ALIYUN_ASR_URL", "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1")
    ALIYUN_ASR_REGION = os.getenv("ALIYUN_ASR_REGION", "cn-shanghai")
    ALIYUN_ASR_TOKEN = os.getenv("ALIYUN_ASR_TOKEN", "")

    @property
    def asr_chunk_size(self) -> list:
        return [int(x.strip()) for x in self.ASR_CHUNK_SIZE_STR.split(",") if x.strip()]

    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")
    TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")
    TTS_VOLUME = float(os.getenv("TTS_VOLUME", "0.8"))
    TTS_PLAYER = os.getenv("TTS_PLAYER", "pygame")

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    PLC_ENABLED = os.getenv("PLC_ENABLED", "false").lower() == "true"
    PLC_PROVIDER = os.getenv("PLC_PROVIDER", "mock")
    PLC_AMS_NET_ID = os.getenv("PLC_AMS_NET_ID", "192.168.1.1.1.1")
    PLC_AMS_PORT = int(os.getenv("PLC_AMS_PORT", "851"))
    PLC_IP_ADDRESS = os.getenv("PLC_IP_ADDRESS", None)
    PLC_TRIGGER_VAR = os.getenv("PLC_TRIGGER_VAR", None)

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", None)
    VERBOSE = os.getenv("VERBOSE", "true").lower() == "true"

    AUDIO_CHUNK = 1024
    AUDIO_FORMAT = 8

    USE_TEMPLATE_MATCHING = os.getenv("USE_TEMPLATE_MATCHING", "true").lower() == "true"

    MONITOR_VARIABLES_STR = os.getenv("MONITOR_VARIABLES", "")
    MONITOR_INTERVAL_MS = int(os.getenv("MONITOR_INTERVAL_MS", "200"))

    VOICE_INPUT_ENABLED = os.getenv("VOICE_INPUT_ENABLED", "true").lower() == "true"
    VOICE_OUTPUT_ENABLED = os.getenv("VOICE_OUTPUT_ENABLED", "true").lower() == "true"
    CONSOLE_INPUT_ENABLED = os.getenv("CONSOLE_INPUT_ENABLED", "false").lower() == "true"
    CONSOLE_OUTPUT_ENABLED = os.getenv("CONSOLE_OUTPUT_ENABLED", "false").lower() == "true"

    DB_ENABLED = os.getenv("DB_ENABLED", "false").lower() == "true"
    DB_TYPE = os.getenv("DB_TYPE", "sqlite")
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "plc_data.db")

    DATA_COLLECTION_ENABLED = os.getenv("DATA_COLLECTION_ENABLED", "false").lower() == "true"
    DATA_COLLECTION_INTERVAL = int(os.getenv("DATA_COLLECTION_INTERVAL", "1000"))
    DATA_COLLECTION_BATCH_SIZE = int(os.getenv("DATA_COLLECTION_BATCH_SIZE", "10"))

    MAPPINGS_FILE = Path(__file__).parent / "variable_mappings.yaml"

    @property
    def mappings(self) -> dict:
        if not self.MAPPINGS_FILE.exists():
            return {}
        with open(self.MAPPINGS_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('mappings', {})

    @property
    def VARIABLE_MAPPINGS(self) -> dict:
        return self.mappings

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