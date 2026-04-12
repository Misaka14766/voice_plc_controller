import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..config.settings import settings
from ..core import get_llm, get_plc
from ..core.llm.openai_llm import set_plc_instance
from ..core.template_matcher import TemplateMatcher

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
    """文本对话接口（无语音）"""
    global conversation_history
    text = request.text.strip()
    if not text:
        return {"response": ""}

    # 模板匹配快速通道
    if settings.USE_TEMPLATE_MATCHING and template_matcher:
        match_result = template_matcher.match(text)
        if match_result:
            op_type, params = match_result
            response_text = template_matcher.execute(op_type, params)
            conversation_history.append({"role": "user", "content": text})
            conversation_history.append({"role": "assistant", "content": response_text})
            return {"response": response_text, "template": True}

    # LLM 处理
    conversation_history.append({"role": "user", "content": text})
    if len(conversation_history) > max_history_turns * 2:
        conversation_history = conversation_history[-max_history_turns * 2:]

    messages = [{"role": m["role"], "content": m["content"]} for m in conversation_history]
    response = await llm.generate(messages=messages)

    conversation_history.append({"role": "assistant", "content": response.content})
    return {"response": response.content, "template": False}


@app.post("/api/plc/read")
async def plc_read(request: PLCReadRequest):
    """读取PLC变量"""
    if not plc or not plc.is_connected():
        return {"success": False, "error": "PLC 未连接"}
    try:
        value = plc.read(request.variable, request.data_type)
        return {"success": True, "value": value}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/plc/write")
async def plc_write(request: PLCWriteRequest):
    """写入PLC变量"""
    if not plc or not plc.is_connected():
        return {"success": False, "error": "PLC 未连接"}
    try:
        success = plc.write(request.variable, request.value, request.data_type)
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/plc/variables")
async def list_variables():
    """获取PLC所有变量"""
    if not plc or not plc.is_connected():
        return {"success": False, "error": "PLC 未连接", "variables": []}
    try:
        symbols = plc.get_all_symbols()
        return {"success": True, "variables": symbols}
    except Exception as e:
        return {"success": False, "error": str(e), "variables": []}


@app.websocket("/ws/asr")
async def websocket_asr(websocket: WebSocket):
    """
    语音识别WebSocket接口
    前端发送音频数据（base64编码的PCM16），后端实时返回识别结果
    """
    await websocket.accept()
    from ..core import get_asr
    asr = get_asr()
    asr.start()
    asr.set_callback(lambda text, is_final: None)  # 同步回调用于内部状态

    full_text = ""

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "audio":
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
            elif data.get("type") == "reset":
                asr.reset()
                full_text = ""
    except WebSocketDisconnect:
        pass
    finally:
        asr.stop()


@app.post("/api/tts")
async def tts_synthesize(request: TextRequest):
    """文本转语音，返回音频base64"""
    from ..core import get_tts
    tts = get_tts()
    audio_bytes = await tts.synthesize_async(request.text)
    audio_b64 = base64.b64encode(audio_bytes).decode()
    return {"audio": audio_b64}


@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "plc_connected": plc.is_connected() if plc else False,
        "asr_provider": settings.ASR_PROVIDER,
        "tts_provider": settings.TTS_PROVIDER,
    }


@app.post("/api/clear")
async def clear_history():
    """清空对话历史"""
    global conversation_history
    conversation_history = []
    return {"success": True}