import base64
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..config.settings import settings
from ..core import get_llm, get_plc, get_asr, get_tts
from ..core.llm.openai_llm import set_plc_instance
from ..core.template_matcher import TemplateMatcher
from ..core.db import DatabaseFactory, DatabaseInterface
from ..core.db.queries import DataQuerier
from ..core.plc.collector import PLCCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice PLC Control API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

plc = get_plc()
set_plc_instance(plc)
llm = get_llm()
template_matcher = TemplateMatcher(plc) if plc else None

db_manager: Optional[DatabaseInterface] = None
data_collector: Optional[PLCCollector] = None

conversation_history = []
max_history_turns = 10


class TextRequest(BaseModel):
    text: str


class PLCReadRequest(BaseModel):
    variable: str
    data_type: str = "INT"


class PLCWriteRequest(BaseModel):
    variable: str
    value: str | int | bool
    data_type: str = "INT"


class SystemStatus(BaseModel):
    plc_connected: bool
    asr_provider: str
    tts_provider: str
    llm_provider: str
    template_matching: bool


@app.on_event("startup")
async def startup_event():
    global db_manager, data_collector

    if plc:
        if plc.connect():
            logger.info("✅ PLC 连接成功")
        else:
            logger.warning("⚠️ PLC 连接失败")

    if settings.DB_ENABLED:
        try:
            if settings.DB_TYPE == "sqlite":
                db_manager = DatabaseFactory.create_database(
                    db_type="sqlite",
                    db_path=settings.SQLITE_DB_PATH
                )
            else:
                logger.error(f"不支持的数据库类型: {settings.DB_TYPE}")
                db_manager = None

            if db_manager and db_manager.connect():
                DataQuerier.init_instance(db_manager)
                logger.info(f"✅ {settings.DB_TYPE.upper()} 数据库连接成功")

                if settings.DATA_COLLECTION_ENABLED and plc:
                    data_collector = PLCCollector(
                        plc=plc,
                        db_manager=db_manager,
                        interval_ms=settings.DATA_COLLECTION_INTERVAL
                    )
                    for var_name, var_type in settings.monitor_variables:
                        data_collector.add_variable(var_name, var_type)

                    if settings.DATA_COLLECTION_BATCH_SIZE > 1:
                        data_collector.set_batch_size(settings.DATA_COLLECTION_BATCH_SIZE)

                    data_collector.start()
                    logger.info(f"✅ 数据采集器已启动，间隔: {settings.DATA_COLLECTION_INTERVAL}ms")
            else:
                logger.error(f"⚠️ {settings.DB_TYPE.upper()} 数据库连接失败")
                db_manager = None
        except Exception as e:
            logger.error(f"⚠️ 数据库初始化失败: {e}")
            db_manager = None


@app.on_event("shutdown")
async def shutdown_event():
    global db_manager, data_collector

    if data_collector:
        data_collector.stop()
        logger.info("数据采集器已停止")

    if db_manager:
        db_manager.disconnect()
        logger.info("数据库连接已关闭")


@app.websocket("/ws/asr")
async def websocket_asr(websocket: WebSocket):
    """WebSocket 实时语音识别"""
    await websocket.accept()
    try:
        asr = get_asr()
        if not asr:
            await websocket.close(code=1000, reason="ASR 服务未初始化")
            return

        await asr.start_streaming(websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket 连接断开")
    except Exception as e:
        logger.error(f"WebSocket 错误: {str(e)}")
        await websocket.close(code=1000, reason=str(e))


@app.post("/api/chat")
async def chat(request: TextRequest):
    """对话接口"""
    try:
        if not llm:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")

        conversation_history.append({"role": "user", "content": request.text})

        if len(conversation_history) > max_history_turns * 2:
            conversation_history[:] = conversation_history[-max_history_turns * 2:]

        response = await llm.generate_async(conversation_history)

        conversation_history.append({"role": "assistant", "content": response})

        return {"response": response, "success": True}
    except Exception as e:
        logger.error(f"对话处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@app.get("/api/plc/variables")
async def list_plc_variables():
    """获取 PLC 变量列表"""
    try:
        if not plc or not plc.is_connected():
            raise HTTPException(status_code=503, detail="PLC 未连接")

        variables = []
        for var_name, var_type in settings.monitor_variables:
            try:
                comment = ""
                if settings.VARIABLE_MAPPINGS and var_name in settings.VARIABLE_MAPPINGS:
                    comment = settings.VARIABLE_MAPPINGS[var_name].get('comment', '')
            except Exception:
                comment = ""

            variables.append({
                "name": var_name,
                "type": var_type,
                "comment": comment
            })

        return {"success": True, "variables": variables}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 PLC 变量列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取 PLC 变量列表失败: {str(e)}")


@app.post("/api/plc/read")
async def plc_read(request: PLCReadRequest):
    """读取 PLC 变量"""
    try:
        if not plc or not plc.is_connected():
            raise HTTPException(status_code=503, detail="PLC 未连接")

        value = plc.read(request.variable, request.data_type)
        return {"variable": request.variable, "value": value, "success": True}
    except Exception as e:
        logger.error(f"读取 PLC 变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"读取 PLC 变量失败: {str(e)}")


@app.post("/api/plc/write")
async def plc_write(request: PLCWriteRequest):
    """写入 PLC 变量"""
    try:
        if not plc or not plc.is_connected():
            raise HTTPException(status_code=503, detail="PLC 未连接")

        plc.write(request.variable, request.value, request.data_type)
        return {"variable": request.variable, "value": request.value, "success": True}
    except Exception as e:
        logger.error(f"写入 PLC 变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"写入 PLC 变量失败: {str(e)}")


@app.post("/api/voice")
async def voice_interaction(request: TextRequest):
    """语音交互接口"""
    try:
        if not llm:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")

        if template_matcher and settings.USE_TEMPLATE_MATCHING:
            result = template_matcher.match_and_execute(request.text)
            if result:
                return {"response": result, "success": True}

        conversation_history.append({"role": "user", "content": request.text})

        if len(conversation_history) > max_history_turns * 2:
            conversation_history[:] = conversation_history[-max_history_turns * 2:]

        response = await llm.generate_async(conversation_history)

        conversation_history.append({"role": "assistant", "content": response})

        if settings.VOICE_OUTPUT_ENABLED:
            tts = get_tts()
            if tts:
                try:
                    audio_bytes = await tts.synthesize_async(response)
                    audio_b64 = base64.b64encode(audio_bytes).decode()
                    return {"response": response, "audio": audio_b64, "success": True}
                except Exception as e:
                    logger.error(f"语音合成失败: {str(e)}")

        return {"response": response, "success": True}
    except Exception as e:
        logger.error(f"语音交互处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"语音交互处理失败: {str(e)}")


@app.post("/api/asr/start")
async def start_asr():
    """启动语音识别"""
    try:
        asr = get_asr()
        if not asr:
            raise HTTPException(status_code=503, detail="ASR 服务未初始化")

        asr.start()
        return {"success": True}
    except Exception as e:
        logger.error(f"启动语音识别失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动语音识别失败: {str(e)}")


@app.post("/api/asr/stop")
async def stop_asr():
    """停止语音识别"""
    try:
        asr = get_asr()
        if not asr:
            raise HTTPException(status_code=503, detail="ASR 服务未初始化")

        asr.stop()
        return {"success": True}
    except Exception as e:
        logger.error(f"停止语音识别失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止语音识别失败: {str(e)}")


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
    try:
        return {
            "asr_provider": settings.ASR_PROVIDER,
            "tts_provider": settings.TTS_PROVIDER,
            "llm_provider": settings.LLM_PROVIDER,
            "plc_enabled": settings.PLC_ENABLED,
            "template_matching": settings.USE_TEMPLATE_MATCHING,
            "voice_input_enabled": settings.VOICE_INPUT_ENABLED,
            "voice_output_enabled": settings.VOICE_OUTPUT_ENABLED,
            "db_enabled": settings.DB_ENABLED,
            "db_type": settings.DB_TYPE,
            "data_collection_enabled": settings.DATA_COLLECTION_ENABLED,
        }
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"系统配置处理失败: {str(e)}")


@app.get("/api/data/realtime")
async def get_realtime_data(
    variables: List[str] = Query(..., description="变量名列表")
):
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="数据库未启用")

        result = DataQuerier.get_realtime(variables)
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实时数据失败: {str(e)}")


@app.get("/api/data/history")
async def get_history_data(
    variable: str = Query(..., description="变量名"),
    hours: int = Query(1, description="查询小时数"),
    aggregation: str = Query("mean", description="聚合函数: mean, max, min, sum, first, last")
):
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="数据库未启用")

        window_seconds = int(hours * 60 * 60 / 100)
        if window_seconds < 60:
            window_seconds = 60

        data = DataQuerier.get_aggregated(
            variable_name=variable,
            hours=hours,
            window_seconds=window_seconds,
            aggregation=aggregation
        )
        return {"success": True, "data": data, "count": len(data)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")


@app.get("/api/data/chart")
async def get_chart_data(
    variable: str = Query(..., description="变量名"),
    time_range: str = Query("1h", description="时间范围: 30m, 1h, 6h, 12h, 24h, 7d"),
    aggregation: str = Query("mean", description="聚合函数")
):
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="数据库未启用")

        data = DataQuerier.get_chart_data(variable, time_range, aggregation)
        return {"success": True, **data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图表数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取图表数据失败: {str(e)}")


@app.get("/api/collector/status")
async def get_collector_status():
    try:
        if not data_collector:
            return {"success": True, "running": False, "message": "数据采集器未启用"}

        status = data_collector.get_status()
        return {"success": True, **status}
    except Exception as e:
        logger.error(f"获取采集器状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取采集器状态失败: {str(e)}")


@app.post("/api/collector/start")
async def start_collector():
    try:
        if not data_collector:
            raise HTTPException(status_code=503, detail="数据采集器未配置")

        if not data_collector.running:
            data_collector.start()
            logger.info("数据采集器已启动")

        return {"success": True, "message": "数据采集器已启动"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动采集器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动采集器失败: {str(e)}")


@app.post("/api/collector/stop")
async def stop_collector():
    try:
        if not data_collector:
            raise HTTPException(status_code=503, detail="数据采集器未配置")

        if data_collector.running:
            data_collector.stop()
            logger.info("数据采集器已停止")

        return {"success": True, "message": "数据采集器已停止"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止采集器失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止采集器失败: {str(e)}")