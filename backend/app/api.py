import base64
import logging
import sys
import traceback
from pathlib import Path
import yaml
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio

# Add root directory to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(ROOT_DIR)

from backend.config.settings import settings
from backend.core import get_llm, get_plc, get_asr, get_tts
from backend.core.llm.openai_llm import set_plc_instance, set_db_manager
from backend.core.template_matcher import TemplateMatcher
from backend.core.db import DatabaseFactory, DatabaseInterface
from backend.core.db.queries import DataQuerier
from backend.core.plc.collector import PLCCollector

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


@app.get("/api/plc/monitor-variables")
async def get_monitor_variables():
    """获取监控变量列表"""
    try:
        return {"success": True, "variables": settings.monitor_variables}
    except Exception as e:
        logger.error(f"获取监控变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取监控变量失败: {str(e)}")


class MonitorVariablesRequest(BaseModel):
    variables: List[Dict[str, str]]  # [{"name": "MAIN.WaterLevel", "type": "REAL"}, ...]


@app.post("/api/plc/monitor-variables")
async def update_monitor_variables(request: MonitorVariablesRequest):
    """更新监控变量列表"""
    try:
        # 从动态配置读取当前配置
        current_config = settings.dynamic_config
        
        # 确保 monitor 部分存在
        if 'monitor' not in current_config:
            current_config['monitor'] = {}
        
        # 将变量列表转换为字符串格式存储
        # 变量格式为 "MAIN.WaterLevel:REAL, MAIN.Temperature:REAL"
        if request.variables:
            variables_with_type = [f"{v['name']}:{v['type']}" for v in request.variables]
            variables_str = ', '.join(variables_with_type)
        else:
            variables_str = ''
        current_config['monitor']['variables'] = variables_str
        
        # 保存回配置文件
        if settings.save_dynamic_config(current_config):
            return {"success": True, "message": "监控变量已更新", "variables": request.variables}
        else:
            raise HTTPException(status_code=500, detail="保存配置文件失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新监控变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新监控变量失败: {str(e)}")


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
                set_db_manager(db_manager)
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

        # 初始化 ASR
        asr.start()
        
        # 获取当前事件循环
        loop = asyncio.get_event_loop()
        
        # 设置回调函数（同步函数，使用loop.call_soon_threadsafe处理跨线程操作）
        def callback(text: str, is_final: bool):
            try:
                # 使用call_soon_threadsafe确保从任何线程安全地调用
                loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(
                        websocket.send_json({
                            "type": "partial" if not is_final else "final",
                            "text": text
                        })
                    )
                )
            except Exception as e:
                logger.error(f"发送识别结果失败: {str(e)}")
                logger.error("完整调用堆栈:")
                traceback.print_exc()
                sys.stderr.write(traceback.format_exc())
        
        asr.set_callback(callback)
        
        # 直接处理前端发送的PCM数据（16位有符号整型，16kHz，单声道）
        logger.info("开始处理PCM音频数据")
        
        # 接收音频数据并直接发送给ASR
        while True:
            try:
                # 前端直接发送PCM数据（ArrayBuffer）
                data = await websocket.receive_bytes()

                logger.debug(f"ASR 收到PCM数据，大小: {len(data)} 字节")
                
                if data:
                    # 检查是否是结束标记（空的字节数据）
                    if len(data) == 0:
                        # 处理结束标记
                        logger.info("收到录音结束标记")
                        
                        # 发送最终数据
                        asr.feed_chunk(b'', is_final=True)
                        logger.info("ASR 处理完成")
                        
                        # 继续等待下一个数据块
                        continue
                    
                    else:
                        # 直接将PCM数据发送给ASR
                        asr.feed_chunk(data, is_final=False)
                            
            except WebSocketDisconnect:
                logger.info("WebSocket 连接断开（在接收数据时）")
                break
            except Exception as e:
                logger.error(f"接收音频数据失败: {str(e)}")
                logger.error("完整调用堆栈:")
                traceback.print_exc()
                sys.stderr.write(traceback.format_exc())
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket 连接断开")
        # 停止 ASR
        if asr:
            asr.stop()
    except Exception as e:
        # 输出完整的错误信息和调用堆栈
        error_msg = f"WebSocket 错误: {str(e)}"
        logger.error(error_msg)
        logger.error("完整调用堆栈:")
        traceback.print_exc()
        sys.stderr.write(traceback.format_exc())
        # 停止 ASR
        if asr:
            asr.stop()
        await websocket.close(code=1000, reason=str(e))
    finally:
        # 确保ASR被停止
        if asr:
            asr.stop()
        logger.info("WebSocket处理结束")


@app.post("/api/chat")
async def chat(request: TextRequest):
    """对话接口"""
    try:
        if not llm:
            raise HTTPException(status_code=503, detail="LLM 服务未初始化")

        conversation_history.append({"role": "user", "content": request.text})

        if len(conversation_history) > max_history_turns * 2:
            conversation_history[:] = conversation_history[-max_history_turns * 2:]

        response = await llm.generate(conversation_history)

        conversation_history.append({"role": "assistant", "content": response.content})

        return {"response": response.content, "success": True}
    except Exception as e:
        logger.error(f"对话处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@app.get("/api/plc/variables")
async def list_plc_variables():
    """获取 PLC 变量列表（所有变量，供监控页面选择）"""
    try:
        if not plc or not plc.is_connected():
            raise HTTPException(status_code=503, detail="PLC 未连接")

        # 获取所有PLC变量
        all_symbols = plc.get_all_symbols()
        variables = []
        for sym in all_symbols:
            var_name = sym.get("name", "")
            var_type = sym.get("type", "UNKNOWN")
            comment = sym.get("comment", "")
            
            # 尝试从mappings获取注释
            if not comment and settings.VARIABLE_MAPPINGS and var_name in settings.VARIABLE_MAPPINGS:
                comment = settings.VARIABLE_MAPPINGS[var_name].get('comment', '')
            
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


@app.get("/api/plc/device-info")
async def get_plc_device_info():
    """获取 PLC 设备信息"""
    try:
        if plc:
            device_info = plc.get_device_info()
            return {
                "success": True,
                "model": device_info.get("model"),
                "system": device_info.get("system"),
                "ipAddress": device_info.get("ip_address"),
                "status": "已连接" if device_info.get("connected", False) else "未连接",
                "modelLink": device_info.get("model_link"),
                "systemLink": device_info.get("system_link")
            }
        else:
            raise HTTPException(status_code=503, detail="PLC 未初始化")
    except Exception as e:
        logger.error(f"获取设备信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取设备信息失败: {str(e)}")


class PLCReadListRequest(BaseModel):
    variables: List[str]


class PLCWriteListRequest(BaseModel):
    variables: Dict[str, Any]


@app.post("/api/plc/read-list")
async def plc_read_list(request: PLCReadListRequest):
    """批量读取 PLC 变量"""
    try:
        if not plc or not plc.is_connected():
            raise HTTPException(status_code=503, detail="PLC 未连接")

        values = plc.read_list(request.variables)
        return {"success": True, "values": values}
    except Exception as e:
        logger.error(f"批量读取 PLC 变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量读取 PLC 变量失败: {str(e)}")


@app.post("/api/plc/write-list")
async def plc_write_list(request: PLCWriteListRequest):
    """批量写入 PLC 变量"""
    try:
        if not plc or not plc.is_connected():
            raise HTTPException(status_code=503, detail="PLC 未连接")

        results = plc.write_list(request.variables)
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"批量写入 PLC 变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量写入 PLC 变量失败: {str(e)}")


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


@app.get("/api/data/variables")
async def get_all_db_variables():
    """获取所有数据库变量"""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="数据库未启用")

        variables = DataQuerier.get_all_variables()
        return {"success": True, "variables": variables}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据库变量失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据库变量失败: {str(e)}")


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


@app.post("/api/db/clear-variable")
async def clear_variable_data(variable: str = Query(..., description="要清空数据的变量名")):
    """清空指定变量的数据"""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="数据库未初始化")

        success = db_manager.clear_variable_data(variable)
        if success:
            return {"success": True, "message": f"变量 {variable} 的数据已清空"}
        else:
            raise HTTPException(status_code=500, detail=f"清空变量 {variable} 的数据失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空变量数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清空变量数据失败: {str(e)}")


@app.post("/api/db/clear-all")
async def clear_all_data():
    """清空所有数据"""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="数据库未初始化")

        success = db_manager.clear_all_data()
        if success:
            return {"success": True, "message": "所有数据已清空"}
        else:
            raise HTTPException(status_code=500, detail="清空所有数据失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空所有数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清空所有数据失败: {str(e)}")


@app.get("/api/knowledge")
async def get_knowledge():
    """获取知识库内容"""
    try:
        kb_path = Path(__file__).parent.parent / "config" / "knowledge_base.yaml"
        if not kb_path.exists():
            return {"success": True, "entries": []}

        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_data = yaml.safe_load(f) or {}

        return {"success": True, "entries": kb_data.get('entries', [])}
    except Exception as e:
        logger.error(f"获取知识库失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取知识库失败: {str(e)}")


@app.post("/api/knowledge")
async def save_knowledge(request: dict):
    """保存知识库内容"""
    try:
        kb_path = Path(__file__).parent.parent / "config" / "knowledge_base.yaml"

        kb_data = {"entries": request.get('entries', [])}

        with open(kb_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(kb_data, f, allow_unicode=True, sort_keys=False)

        return {"success": True, "message": "知识库已保存"}
    except Exception as e:
        logger.error(f"保存知识库失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存知识库失败: {str(e)}")


@app.get("/api/knowledge/test")
async def test_knowledge_recall(query: str = Query("", description="测试查询")):
    """测试知识召回"""
    try:
        kb_path = Path(__file__).parent.parent / "config" / "knowledge_base.yaml"
        if not kb_path.exists():
            return {"success": True, "result": "知识库文件不存在"}

        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_data = yaml.safe_load(f) or {}

        entries = kb_data.get('entries', [])
        if not entries:
            return {"success": True, "result": "知识库为空"}

        if not query:
            matched = entries[:5]
        else:
            query_lower = query.lower()
            matched = [e for e in entries if query_lower in e.get('question', '').lower() or query_lower in e.get('answer', '').lower()]
            if not matched:
                matched = entries[:5]

        result = "找到相关知识库内容：\n"
        for entry in matched:
            result += f"\n问题: {entry.get('question', '')}\n"
            result += f"答案: {entry.get('answer', '')}\n"

        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"测试知识召回失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@app.get("/api/config")
async def get_config():
    """获取当前配置"""
    try:
        from config.settings import settings
        config = settings.dynamic_config
        return {"success": True, "config": config}
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@app.post("/api/config")
async def update_config(config: dict):
    """更新配置"""
    try:
        from config.settings import settings
        success = settings.save_dynamic_config(config)
        if success:
            return {"success": True, "message": "配置更新成功"}
        else:
            raise HTTPException(status_code=500, detail="配置保存失败")
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


class SystemMetrics(BaseModel):
    cpu: float
    memory: float
    network: float
    uptime: str


@app.get("/api/system/metrics")
async def get_system_metrics():
    """获取系统性能指标"""
    try:
        import psutil
        import time
        from datetime import timedelta
        
        # 获取CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 获取内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 获取网络带宽（最近1秒内的发送和接收字节数）
        net_io = psutil.net_io_counters()
        time.sleep(1)
        net_io2 = psutil.net_io_counters()
        network_bytes = (net_io2.bytes_sent - net_io.bytes_sent) + (net_io2.bytes_recv - net_io.bytes_recv)
        network_mbps = (network_bytes * 8) / (1024 * 1024)
        
        # 获取系统运行时间
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_str = str(timedelta(seconds=int(uptime_seconds)))
        
        return SystemMetrics(
            cpu=round(cpu_percent, 1),
            memory=round(memory_percent, 1),
            network=round(network_mbps, 1),
            uptime=uptime_str
        )
    except ImportError:
        # 如果psutil未安装，返回模拟数据
        return SystemMetrics(
            cpu=35.5,
            memory=55.2,
            network=75.8,
            uptime="72:34:15"
        )
    except Exception as e:
        logger.error(f"获取系统性能指标失败: {str(e)}")
        # 发生错误时返回默认值
        return SystemMetrics(
            cpu=0.0,
            memory=0.0,
            network=0.0,
            uptime="00:00:00"
        )