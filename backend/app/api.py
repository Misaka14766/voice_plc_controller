import base64
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..config.settings import settings
from ..core import get_llm, get_plc, get_asr, get_tts
from ..core.llm.openai_llm import set_plc_instance
from ..core.template_matcher import TemplateMatcher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice PLC Control API")

# 允许跨域（开发时可设 "*"，生产环境改为具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化核心组件
plc = get_plc()
set_plc_instance(plc)
llm = get_llm()
template_matcher = TemplateMatcher(plc) if plc else None

# 对话历史存储（简单内存存储，生产环境可换Redis）
conversation_history = []
max_history_turns = 10


class TextRequest(BaseModel):
    text: str


class PLCReadRequest(BaseModel):
    variable: str
    data_type: str = "INT"


class PLCWriteRequest(BaseModel):
    variable: str
    value: str
    data_type: str = "INT"


class SystemStatus(BaseModel):
    plc_connected: bool
    asr_provider: str
    tts_provider: str
    llm_provider: str
    template_matching: bool


@app.on_event("startup")
async def startup_event():
    """启动时连接PLC"""
    if plc:
        if plc.connect():
            print("✅ PLC 连接成功")
        else:
            print("⚠️ PLC 连接失败")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时断开PLC"""
    if plc:
        plc.disconnect()


@app.post("/api/chat")
async def chat(request: TextRequest):
    """文本对话接口"""
    try:
        global conversation_history
        text = request.text.strip()
        if not text:
            return {"response": "", "template": False}

        # 模板匹配快速通道
        if settings.USE_TEMPLATE_MATCHING and template_matcher:
            try:
                match_result = template_matcher.match(text)
                if match_result:
                    op_type, params = match_result
                    response_text = template_matcher.execute(op_type, params)
                    conversation_history.append({"role": "user", "content": text})
                    conversation_history.append({"role": "assistant", "content": response_text})
                    return {"response": response_text, "template": True}
            except Exception as e:
                logger.error(f"模板匹配失败: {str(e)}")
                # 模板匹配失败后继续使用LLM处理

        # LLM 处理
        conversation_history.append({"role": "user", "content": text})
        if len(conversation_history) > max_history_turns * 2:
            conversation_history = conversation_history[-max_history_turns * 2:]

        messages = [{"role": m["role"], "content": m["content"]} for m in conversation_history]
        response = await llm.generate(messages=messages)

        conversation_history.append({"role": "assistant", "content": response.content})
        return {"response": response.content, "template": False}
    except Exception as e:
        logger.error(f"对话接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@app.post("/api/plc/read")
async def plc_read(request: PLCReadRequest):
    """读取PLC变量"""
    try:
        if not plc or not plc.is_connected():
            return {"success": False, "error": "PLC 未连接", "value": None}
        try:
            value = plc.read(request.variable, request.data_type)
            return {"success": True, "value": value, "error": None}
        except Exception as e:
            logger.error(f"读取PLC变量失败: {str(e)}")
            return {"success": False, "error": str(e), "value": None}
    except Exception as e:
        logger.error(f"PLC读取接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PLC读取处理失败: {str(e)}")


@app.post("/api/plc/write")
async def plc_write(request: PLCWriteRequest):
    """写入PLC变量"""
    try:
        if not plc or not plc.is_connected():
            return {"success": False, "error": "PLC 未连接"}
        try:
            success = plc.write(request.variable, request.value, request.data_type)
            return {"success": success, "error": None if success else "写入失败"}
        except Exception as e:
            logger.error(f"写入PLC变量失败: {str(e)}")
            return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"PLC写入接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PLC写入处理失败: {str(e)}")


@app.get("/api/plc/variables")
async def list_variables():
    """获取PLC所有变量"""
    try:
        if not plc or not plc.is_connected():
            return {"success": False, "error": "PLC 未连接", "variables": []}
        try:
            symbols = plc.get_all_symbols()
            return {"success": True, "variables": symbols, "error": None}
        except Exception as e:
            logger.error(f"获取PLC变量列表失败: {str(e)}")
            return {"success": False, "error": str(e), "variables": []}
    except Exception as e:
        logger.error(f"PLC变量列表接口错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PLC变量列表处理失败: {str(e)}")


@app.websocket("/ws/asr")
async def websocket_asr(websocket: WebSocket):
    """
    语音识别WebSocket接口
    前端发送音频数据（base64编码的PCM16），后端实时返回识别结果
    """
    asr = None
    try:
        await websocket.accept()
        asr = get_asr()
        asr.start()
        asr.set_callback(lambda text, is_final: None)  # 同步回调用于内部状态

        full_text = ""

        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "audio":
                    try:
                        # 解码base64音频数据
                        audio_bytes = base64.b64decode(data["data"])
                        is_final = data.get("is_final", False)

                        # 送入ASR
                        result = asr.feed_chunk(audio_bytes, is_final=is_final)

                        # 返回识别结果
                        await websocket.send_json({
                            "type": "partial" if not is_final else "final",
                            "text": result
                        })

                        if is_final:
                            full_text = result
                            asr.reset()
                            break
                    except Exception as e:
                        logger.error(f"处理音频数据失败: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "text": f"处理音频数据失败: {str(e)}"
                        })
                        break
                elif data.get("type") == "reset":
                    asr.reset()
                    full_text = ""
        except WebSocketDisconnect:
            logger.info("WebSocket连接已断开")
        except Exception as e:
            logger.error(f"WebSocket处理错误: {str(e)}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "text": f"WebSocket处理错误: {str(e)}"
                })
            except:
                pass
    except Exception as e:
        logger.error(f"WebSocket连接错误: {str(e)}")
    finally:
        if asr:
            try:
                asr.stop()
            except:
                pass


@app.post("/api/tts")
async def tts_synthesize(request: TextRequest):
    """文本转语音，返回音频base64"""
    try:
        tts = get_tts()
        audio_bytes = await tts.synthesize_async(request.text)
        audio_b64 = base64.b64encode(audio_bytes).decode()
        return {"audio": audio_b64, "success": True}
    except Exception as e:
        logger.error(f"语音合成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"语音合成处理失败: {str(e)}")


@app.get("/api/health")
async def health():
    """健康检查"""
    try:
        return {
            "status": "ok",
            "plc_connected": plc.is_connected() if plc else False,
            "asr_provider": settings.ASR_PROVIDER,
            "tts_provider": settings.TTS_PROVIDER,
            "llm_provider": settings.LLM_PROVIDER,
            "template_matching": settings.USE_TEMPLATE_MATCHING,
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查处理失败: {str(e)}")


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    try:
        return SystemStatus(
            plc_connected=plc.is_connected() if plc else False,
            asr_provider=settings.ASR_PROVIDER,
            tts_provider=settings.TTS_PROVIDER,
            llm_provider=settings.LLM_PROVIDER,
            template_matching=settings.USE_TEMPLATE_MATCHING,
        )
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"系统状态处理失败: {str(e)}")


@app.post("/api/clear")
async def clear_history():
    """清空对话历史"""
    try:
        global conversation_history
        conversation_history = []
        return {"success": True}
    except Exception as e:
        logger.error(f"清空对话历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清空对话历史处理失败: {str(e)}")


@app.get("/api/history")
async def get_history():
    """获取对话历史"""
    try:
        return {"history": conversation_history, "success": True}
    except Exception as e:
        logger.error(f"获取对话历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"对话历史处理失败: {str(e)}")


@app.get("/api/config")
async def get_config():
    """获取系统配置"""
    try:
        return {
            "asr_provider": settings.ASR_PROVIDER,
            "tts_provider": settings.TTS_PROVIDER,
            "llm_provider": settings.LLM_PROVIDER,
            "plc_enabled": settings.PLC_ENABLED,
            "template_matching": settings.USE_TEMPLATE_MATCHING,
            "voice_input_enabled": settings.VOICE_INPUT_ENABLED,
            "voice_output_enabled": settings.VOICE_OUTPUT_ENABLED,
        }
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"系统配置处理失败: {str(e)}")
