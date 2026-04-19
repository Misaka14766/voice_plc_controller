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
def analyze_water_level(hours: int = 1) -> str:
    """分析水位数据，包括当前值、变化趋势、异常检测等。hours为分析的历史时间范围（小时），默认1小时"""
    if _db_manager is None:
        return "数据库未连接，无法分析水位数据"
    try:
        from backend.core.db.queries import DataQuerier
        DataQuerier.init_instance(_db_manager)
        
        water_level_var = None
        for name, info in settings.mappings.items():
            if '水位' in name or '液位' in name or '液面' in name:
                water_level_var = info['variable']
                break
        
        if not water_level_var:
            water_level_var = 'MAIN.IN'
        
        data = DataQuerier.get_aggregated(
            variable_name=water_level_var,
            hours=hours,
            window_seconds=max(60, int(hours * 60 * 60 / 100)),
            aggregation='mean'
        )
        
        if not data or len(data) == 0:
            return f"在过去的{hours}小时内未找到水位数据"
        
        values = [d.get('value', 0) for d in data if d.get('value') is not None]
        if not values:
            return f"在过去的{hours}小时内水位数据无效"
        
        current = values[-1] if values else 0
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        
        trend = "稳定"
        if len(values) >= 2:
            recent = values[-3:] if len(values) >= 3 else values[-2:]
            if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
                trend = "上升"
            elif all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
                trend = "下降"
        
        warnings = []
        for name, info in settings.mappings.items():
            if '水位' in name or '液位' in name or '液面' in name:
                if 'min' in info:
                    if current <= info['min']:
                        warnings.append(f"水位低于最低阈值{info['min']}")
                if 'max' in info:
                    if current >= info['max']:
                        warnings.append(f"水位高于最高阈值{info['max']}")
        
        result = f"水位分析报告（过去{hours}小时）：\n"
        result += f"- 当前值：{current:.2f}\n"
        result += f"- 平均值：{avg_val:.2f}\n"
        result += f"- 最小值：{min_val:.2f}\n"
        result += f"- 最大值：{max_val:.2f}\n"
        result += f"- 趋势：{trend}\n"
        if warnings:
            result += f"- ⚠️ 警告：{'；'.join(warnings)}\n"
        
        return result
    except Exception as e:
        return f"水位分析失败：{e}"

@tool
def query_historical_data(variable: str, hours: int = 1, aggregation: str = "mean") -> str:
    """查询历史数据，用于分析变量的历史趋势。variable为变量名，hours为查询时间范围（小时），aggregation为聚合方式(mean/max/min/sum)"""
    if _db_manager is None:
        return "数据库未连接"
    try:
        from backend.core.db.queries import DataQuerier
        DataQuerier.init_instance(_db_manager)
        
        var_path = variable
        for name, info in settings.mappings.items():
            if name == variable or info['variable'] == variable:
                var_path = info['variable']
                break
        
        data = DataQuerier.get_aggregated(
            variable_name=var_path,
            hours=hours,
            window_seconds=max(60, int(hours * 60 * 60 / 100)),
            aggregation=aggregation
        )
        
        if not data or len(data) == 0:
            return f"在过去的{hours}小时内未找到变量{variable}的数据"
        
        values = [d.get('value', 0) for d in data if d.get('value') is not None]
        if not values:
            return f"变量{variable}在过去的{hours}小时内数据无效"
        
        current = values[-1] if values else 0
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        
        return (f"变量 {variable} 历史数据（过去{hours}小时，{aggregation}聚合）：\n"
                f"- 当前值：{current:.2f}\n"
                f"- 平均值：{avg_val:.2f}\n"
                f"- 最小值：{min_val:.2f}\n"
                f"- 最大值：{max_val:.2f}\n"
                f"- 数据点数：{len(values)}")
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

    当用户询问以下问题时，应调用此工具：
    - "如何设置/操作XXX"
    - "XXX不工作/出错了"
    - "怎么查看/分析XXX"
    - "XXX故障怎么解决"
    - 任何关于系统使用、故障排除的问题
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
        self.tools = [plc_read, plc_write, plc_list_variables, analyze_water_level, query_historical_data, get_knowledge_base]
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
            "- 若用户询问水位分析、趋势、异常等情况，请调用 `analyze_water_level` 工具。\n"
            "- 若用户询问历史数据、历史趋势等，请调用 `query_historical_data` 工具。\n"
            "- 若用户询问系统操作、故障排除、维护等问题，请调用 `get_knowledge_base` 工具。\n"
            "  常见场景：\n"
            "  * 用户说'如何设置水位'、'怎么操作XXX'时调用\n"
            "  * 用户说'XXX不工作了'、'出错了'、'故障'时调用\n"
            "  * 用户询问'怎么查看历史'、'分析趋势'时调用\n"
            "  * 用户询问任何关于系统使用的问题时优先调用\n"
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