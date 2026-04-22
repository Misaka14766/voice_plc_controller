from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from pathlib import Path

from .base import BaseLLM, LLMResponse
from backend.config import settings

_plc_instance = None
_db_manager = None

def set_plc_instance(plc):
    global _plc_instance
    _plc_instance = plc

def set_db_manager(db):
    global _db_manager
    _db_manager = db

@tool
def plc_read(variable: str, data_type: str = "INT") -> str:
    """读取 PLC 变量值。variable 为变量完整路径（如 MAIN.TestInt），data_type 可选 BOOL/INT/REAL/STRING"""
    if _plc_instance is None:
        return "PLC 未连接"
    try:
        val = _plc_instance.read(variable, data_type)
        return f"{variable} 当前值为 {val}"
    except Exception as e:
        return f"读取失败：{e}"

@tool
def plc_write(variable: str, value: str, data_type: str = "INT") -> str:
    """写入 PLC 变量。variable 为变量完整路径，value 为要写入的值，data_type 可选 BOOL/INT/REAL/STRING"""
    if _plc_instance is None:
        return "PLC 未连接"
    success = _plc_instance.write(variable, value, data_type)
    if success:
        return f"成功将 {variable} 设置为 {value}"
    else:
        return f"写入 {variable} 失败，请检查变量名或类型"

@tool
def plc_list_variables() -> str:
    """列出 PLC 中所有可访问的变量（真实从 PLC 获取），同时包含配置的物理名称映射"""
    if _plc_instance is None:
        return "PLC 未连接"
    try:
        symbols = _plc_instance.get_all_symbols()
        if not symbols:
            return "未找到任何 PLC 变量，请检查连接或程序配置"

        lines = ["PLC 中可访问的变量列表："]
        mappings = settings.mappings
        reverse_map = {info['variable']: name for name, info in mappings.items()}

        for sym in symbols:
            name = sym.get('name', '')
            var_type = sym.get('type', 'UNKNOWN')
            comment = sym.get('comment', '')
            physical_hint = reverse_map.get(name, '')
            if physical_hint:
                physical_hint = f" (物理名: {physical_hint})"
            lines.append(f"- {name} : {var_type}{physical_hint} {comment}")

        return "\n".join(lines)
    except Exception as e:
        return f"获取变量列表失败：{e}"



@tool
def query_historical_data(
    variable: str, 
    hours: int = 1, 
    aggregation: str = "mean",
    start_time: str = None, 
    end_time: str = None,
    data_points: int = 100
) -> str:
    """查询历史数据，用于分析变量的历史趋势。
    
    Args:
        variable: 变量名（物理名称或PLC变量路径）
        hours: 查询时间范围（小时），当未指定start_time时使用
        aggregation: 聚合方式(mean/max/min/sum/first/last)
        start_time: 开始时间（ISO格式字符串，如2024-01-01T00:00:00）
        end_time: 结束时间（ISO格式字符串，默认为当前时间）
        data_points: 期望的数据点数量，用于自动计算时间窗口
    """
    if _db_manager is None:
        return "数据库未连接"
    try:
        from backend.core.db.queries import DataQuerier
        from datetime import datetime, timedelta
        DataQuerier.init_instance(_db_manager)
        
        var_path = variable
        for name, info in settings.mappings.items():
            if name == variable or info['variable'] == variable:
                var_path = info['variable']
                break
        
        # 处理时间参数
        if end_time:
            end_time_obj = datetime.fromisoformat(end_time)
        else:
            end_time_obj = datetime.now()
        
        if start_time:
            start_time_obj = datetime.fromisoformat(start_time)
            hours = (end_time_obj - start_time_obj).total_seconds() / 3600
        else:
            start_time_obj = end_time_obj - timedelta(hours=hours)
        
        # 计算窗口大小以获得期望的数据点数量
        total_seconds = (end_time_obj - start_time_obj).total_seconds()
        window_seconds = max(1, int(total_seconds / data_points))
        
        # 获取聚合数据
        data = DataQuerier.get_aggregated(
            variable_name=var_path,
            hours=hours,
            window_seconds=window_seconds,
            aggregation=aggregation,
            end_time=end_time_obj
        )
        
        if not data or len(data) == 0:
            return f"未找到变量{variable}的历史数据"
        
        values = [d.get('value', 0) for d in data if d.get('value') is not None]
        if not values:
            return f"变量{variable}的历史数据无效"
        
        # 计算统计信息
        current = values[-1] if values else 0
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        
        # 计算趋势
        trend = "稳定"
        if len(values) >= 2:
            recent = values[-5:] if len(values) >= 5 else values[-2:]
            if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
                trend = "上升"
            elif all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
                trend = "下降"
        
        # 构建返回结果
        result = f"变量 {variable} 历史数据分析：\n"
        result += f"- 时间范围：{start_time_obj.strftime('%Y-%m-%d %H:%M:%S')} 至 {end_time_obj.strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"- 聚合方式：{aggregation}\n"
        result += f"- 当前值：{current:.2f}\n"
        result += f"- 平均值：{avg_val:.2f}\n"
        result += f"- 最小值：{min_val:.2f}\n"
        result += f"- 最大值：{max_val:.2f}\n"
        result += f"- 趋势：{trend}\n"
        result += f"- 数据点数：{len(values)}\n"
        
        # 当数据点较少时，返回具体数据点
        if len(data) <= 100:
            result += "\n详细数据点：\n"
            for i, point in enumerate(data):
                timestamp = point.get('timestamp', '')
                value = point.get('value', 0)
                result += f"  [{i+1}] {timestamp}: {value:.2f}\n"
        else:
            result += f"\n（数据点较多，仅显示统计信息）"
        
        return result
    except Exception as e:
        return f"查询历史数据失败：{e}"

@tool
def get_knowledge_base(topic: str = "") -> str:
    """获取知识库内容，用于回答用户关于系统操作、故障排除等问题。topic为可选的搜索主题关键词。

    常用主题关键词：
    - 水位、液位、液面：与水位设置和监控相关
    - 温度、加热器：与温度控制和加热器相关
    - 报警、安全：与系统报警和安全机制相关
    - 数据采集、故障排除、维护：与系统维护和故障处理相关
    - 历史数据、查询：与历史数据查询相关
    """
    try:
        kb_path = Path(__file__).parent.parent.parent / "knowledge_base.yaml"
        if not kb_path.exists():
            return "知识库文件不存在"

        import yaml
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_data = yaml.safe_load(f) or {}

        entries = kb_data.get('entries', [])
        if not topic:
            if not entries:
                return "知识库为空"
            result = "知识库内容：\n"
            for entry in entries[:10]:
                result += f"- {entry.get('question', '')}: {entry.get('answer', '')}\n"
            if len(entries) > 10:
                result += f"\n（还有{len(entries)-10}条内容）"
            return result

        matched = []
        for entry in entries:
            q = entry.get('question', '').lower()
            a = entry.get('answer', '').lower()
            t = entry.get('tags', [])
            topic_lower = topic.lower()
            if topic_lower in q or topic_lower in a or topic_lower in t:
                matched.append(entry)

        if not matched:
            return f"未找到与'{topic}'相关的知识库条目"

        result = f"找到{len(matched)}条相关知识库内容：\n"
        for entry in matched[:5]:
            result += f"- {entry.get('question', '')}: {entry.get('answer', '')}\n"
        return result
    except Exception as e:
        return f"获取知识库失败：{e}"


class OpenAICompatibleLLM(BaseLLM):
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        self.tools = [plc_read, plc_write, plc_list_variables, query_historical_data, get_knowledge_base]
        self.system_prompt = self._build_system_prompt()
        self._agent = None

    def _build_system_prompt(self) -> str:
        """构建包含物理映射信息及强制工具使用规则的提示词"""
        base_prompt = (
            "你是工业语音助手，可控制PLC。回答要简短，适合语音播报。\n\n"
            "⚠️ 重要规则：\n"
            "- 任何涉及读取 PLC 变量值的操作，你必须调用 `plc_read` 工具获取实时数据。\n"
            "- 任何涉及修改 PLC 变量值的操作，你必须调用 `plc_write` 工具执行写入。\n"
            "- 严禁凭空编造或猜测变量值，必须通过工具获取真实数据。\n"
            "- 若用户询问当前有哪些可用变量，请调用 `plc_list_variables` 获取列表。\n"
            "- 若用户询问历史数据、历史趋势等，请调用 `query_historical_data` 工具。\n"
            "- 若用户询问系统操作、故障排除、维护等问题，请调用 `get_knowledge_base` 工具。\n"
        )
        mappings = settings.mappings
        if mappings:
            mapping_text = "\n当前配置的物理名称映射：\n"
            for physical_name, info in mappings.items():
                mapping_text += (
                    f"- 物理名称: {physical_name} -> 变量路径: {info['variable']}, "
                    f"类型: {info.get('type', 'REAL')}, "
                    f"描述: {info.get('description', '')}\n"
                )
            mapping_text += "\n当用户使用物理名称时，优先使用对应的变量路径调用工具。"
            return base_prompt + mapping_text
        return base_prompt

    def _get_agent(self):
        if self._agent is None:
            self._agent = create_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=self.system_prompt,
            )
        return self._agent

    async def generate(self, messages, tools=None):
        if not messages:
            return LLMResponse(content="")

        langchain_messages = []
        for msg in messages:
            if msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        agent = self._get_agent()
        result = await agent.ainvoke({"messages": langchain_messages})

        response_content = ""
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            response_content = last_message.content

        return LLMResponse(content=response_content)