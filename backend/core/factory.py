from backend.config import settings

def get_asr():
    if settings.ASR_PROVIDER == "funasr":
        from backend.core.asr.funasr_asr import FunASRStream
        return FunASRStream()
    elif settings.ASR_PROVIDER == "aliyun":
        from backend.core.asr.aliyun_asr import AliyunASR
        return AliyunASR()
    else:
        raise ValueError(f"Unknown ASR provider: {settings.ASR_PROVIDER}")

def get_tts():
    if settings.TTS_PROVIDER == "edge":
        from backend.core.tts.edge_tts import EdgeTTS
        return EdgeTTS()
    raise ValueError(f"Unknown TTS provider: {settings.TTS_PROVIDER}")

def get_llm():
    if settings.LLM_PROVIDER == "openai":
        from backend.core.llm.openai_llm import OpenAICompatibleLLM
        return OpenAICompatibleLLM()
    raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")

def get_plc():
    if not settings.PLC_ENABLED:
        return None
    if settings.PLC_PROVIDER == "beckhoff":
        from backend.core.plc.beckhoff_plc import BeckhoffPLC
        return BeckhoffPLC()
    elif settings.PLC_PROVIDER == "mock":
        from backend.core.plc.mock_plc import MockPLC
        return MockPLC()
    raise ValueError(f"Unknown PLC provider: {settings.PLC_PROVIDER}")